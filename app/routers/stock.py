import hashlib
import json
from datetime import datetime, timedelta
from threading import Lock
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import and_, case, desc, func, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas_stock
from app.database import get_db
from app.dependencies import require_ui_access
from app.routers.web import (
    ensure_indexes,
    get_all_distinct_tags,
    get_program_tags,
    normalize_program_tags,
)
from app.services import cleanup_service

router = APIRouter(
    prefix="/api/v1/stock",
    tags=["stock-management"],
    dependencies=[Depends(require_ui_access)],
)


_STOCK_CENTER_TRIGGER_VERSION = 1
_STOCK_CENTER_CACHE_CONTROL = "private, max-age=0, must-revalidate"
_STOCK_CENTER_REVISION_LOCK = Lock()


def _ensure_stock_center_revision(db: Session) -> Optional[int]:
    """Return a durable, exact invalidation counter for stock-center data.

    The stock center combines product rows, current point history, program
    metadata and stock history.  A COUNT/MAX signature can collide when a row
    is edited or when rows are deleted and re-created, which would make a
    conditional request return stale inventory.  SQLite triggers instead
    increment one counter for every insert/update/delete on each source table.
    The counter is read with one indexed lookup after the one-time setup.

    The application currently uses SQLite.  Other SQLAlchemy backends fall
    back to an exact response-body digest, so this helper intentionally returns
    ``None`` there rather than claiming that an approximate revision is safe.
    """
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "sqlite":
        return None

    try:
        with _STOCK_CENTER_REVISION_LOCK:
            try:
                row = db.execute(text(
                    "SELECT revision, trigger_version "
                    "FROM stock_center_revision WHERE id = 1"
                )).first()
            except SQLAlchemyError:
                # The table is created lazily so old databases do not need a
                # separate migration.  Roll back the failed SELECT before
                # issuing DDL; if the error was unrelated, the outer handler
                # will conservatively fall back to a body digest.
                db.rollback()
                db.execute(text(
                    "CREATE TABLE IF NOT EXISTS stock_center_revision ("
                    "id INTEGER PRIMARY KEY CHECK (id = 1), "
                    "revision INTEGER NOT NULL DEFAULT 0, "
                    "trigger_version INTEGER NOT NULL DEFAULT 0"
                    ")"
                ))
                db.execute(text(
                    "INSERT OR IGNORE INTO stock_center_revision "
                    "(id, revision, trigger_version) VALUES (1, 0, 0)"
                ))
                row = db.execute(text(
                    "SELECT revision, trigger_version "
                    "FROM stock_center_revision WHERE id = 1"
                )).first()

            if row is None:
                db.execute(text(
                    "INSERT OR IGNORE INTO stock_center_revision "
                    "(id, revision, trigger_version) VALUES (1, 0, 0)"
                ))
                row = (0, 0)

            if int(row[1] or 0) < _STOCK_CENTER_TRIGGER_VERSION:
                trigger_tables = (
                    "products",
                    "points_history",
                    "mini_programs",
                    "stock_history",
                )
                trigger_events = (("INSERT", "ai"), ("UPDATE", "au"), ("DELETE", "ad"))
                for table_name in trigger_tables:
                    for event_name, suffix in trigger_events:
                        db.execute(text(
                            f"CREATE TRIGGER IF NOT EXISTS "
                            f"stock_center_revision_{table_name}_{suffix} "
                            f"AFTER {event_name} ON {table_name} "
                            "BEGIN "
                            "UPDATE stock_center_revision "
                            "SET revision = revision + 1 WHERE id = 1; "
                            "END"
                        ))
                db.execute(text(
                    "UPDATE stock_center_revision SET trigger_version = :version "
                    "WHERE id = 1"
                ), {"version": _STOCK_CENTER_TRIGGER_VERSION})

            db.commit()
            revision = db.execute(text(
                "SELECT revision FROM stock_center_revision WHERE id = 1"
            )).scalar()
            return int(revision or 0)
    except SQLAlchemyError:
        db.rollback()
        return None


def _stock_center_cache_key(
    *,
    page: int,
    size: int,
    keyword: str,
    selected_tag: str,
    status: str,
    price_mode: str,
    cash_max: Optional[float],
) -> dict:
    return {
        "page": page,
        "size": size,
        "q": keyword,
        "tag": selected_tag,
        "status": status,
        "price_mode": price_mode,
        "cash_max": cash_max,
    }


def _build_stock_center_etag(revision: object, cache_key: dict, prefix: str = "revision") -> str:
    payload = json.dumps(
        {"revision": revision, "query": cache_key},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f'"stock-center-{prefix}-{digest}"'


def _build_stock_center_body_etag(payload: dict, cache_key: dict) -> str:
    serialized = json.dumps(
        {"body": payload, "query": cache_key},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f'"stock-center-body-{digest}"'


def _if_none_match_matches(request: Optional[Request], etag: str) -> bool:
    if request is None:
        return False
    header = request.headers.get("if-none-match")
    if not header:
        return False

    expected = etag[2:] if etag.startswith("W/") else etag
    for candidate in header.split(","):
        candidate = candidate.strip()
        if candidate == "*":
            return True
        if candidate.startswith("W/"):
            candidate = candidate[2:]
        if candidate == expected:
            return True
    return False


def _stock_center_headers(etag: str) -> dict:
    return {
        "ETag": etag,
        "Cache-Control": _STOCK_CENTER_CACHE_CONTROL,
    }


def ensure_product_columns(db: Session):
    expected_columns = {
        "is_hidden": "ALTER TABLE products ADD COLUMN is_hidden INTEGER DEFAULT 0",
        "hidden_at": "ALTER TABLE products ADD COLUMN hidden_at DATETIME",
        "is_unlisted": "ALTER TABLE products ADD COLUMN is_unlisted INTEGER DEFAULT 0",
        "unlisted_at": "ALTER TABLE products ADD COLUMN unlisted_at DATETIME",
        # 积分加钱购：商品所需现金（元）。NULL/0 = 纯积分商品。
        "cash": "ALTER TABLE products ADD COLUMN cash REAL DEFAULT 0",
    }

    connection = db.bind.connect()
    try:
        inspector = db.bind.dialect.get_columns(connection, "products")
        column_names = {column["name"] for column in inspector}
    finally:
        connection.close()

    # 第一次添加 is_unlisted 列时，把所有原本 is_hidden=1 的商品（之前手动隐藏 + 自动下架混在一起）
    # 一次性迁移到 is_unlisted=1，并清空 is_hidden。这样从今往后两块完全独立。
    needs_migrate_hidden_to_unlisted = "is_unlisted" not in column_names

    missing_statements = [
        statement
        for column_name, statement in expected_columns.items()
        if column_name not in column_names
    ]
    if not missing_statements:
        return

    for statement in missing_statements:
        db.execute(text(statement))

    if needs_migrate_hidden_to_unlisted:
        db.execute(text(
            "UPDATE products SET is_unlisted = 1, unlisted_at = hidden_at, "
            "is_hidden = 0, hidden_at = NULL WHERE is_hidden = 1"
        ))

    db.commit()



def visible_product_filter():
    return and_(
        or_(models.Product.is_hidden == 0, models.Product.is_hidden.is_(None)),
        or_(models.Product.is_unlisted == 0, models.Product.is_unlisted.is_(None)),
    )



def hidden_product_filter():
    return models.Product.is_hidden == 1



def unlisted_product_filter():
    return models.Product.is_unlisted == 1



def normalize_stock_image_url(product: models.Product) -> Optional[str]:
    if product.image_local_path:
        path_str = str(product.image_local_path)
        if path_str.startswith("/static/"):
            return path_str
        if path_str.startswith("static/"):
            return "/" + path_str
        if "/static/" in path_str:
            idx = path_str.find("/static/")
            return path_str[idx:]
        return path_str
    if product.image_url:
        return str(product.image_url)
    return None


@router.post("/product", response_model=schemas_stock.ProductResponse)
def create_or_update_product(
    product_in: schemas_stock.ProductCreateUpdate,
    db: Session = Depends(get_db),
):
    ensure_product_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == product_in.program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail=f"Mini Program with ID '{product_in.program_id}' not found. Please create the program first.")

    product_id = product_in.product_id or product_in.product_name
    product = db.query(models.Product).filter(
        models.Product.program_id == product_in.program_id,
        models.Product.product_id == product_id,
    ).first()

    if product:
        product.product_name = product_in.product_name
        product.image_url = product_in.image_url
        product.points = product_in.points
        product.cash = float(product_in.cash or 0)
        if product_in.stock is not None and product.stock != product_in.stock:
            history = models.StockHistory(
                program_id=product.program_id,
                product_id=product.product_id,
                old_stock=product.stock,
                new_stock=product_in.stock,
                change_time=datetime.utcnow(),
            )
            db.add(history)
            product.stock = product_in.stock
    else:
        product = models.Product(
            program_id=product_in.program_id,
            product_id=product_id,
            product_name=product_in.product_name,
            image_url=product_in.image_url,
            points=product_in.points,
            cash=float(product_in.cash or 0),
            stock=product_in.stock if product_in.stock is not None else 0,
            is_hidden=0,
            hidden_at=None,
        )
        db.add(product)
        history = models.StockHistory(
            program_id=product_in.program_id,
            product_id=product_id,
            old_stock=0,
            new_stock=product_in.stock if product_in.stock is not None else 0,
            change_time=datetime.utcnow(),
        )
        db.add(history)

    try:
        settings = cleanup_service.get_or_create_settings(db)
        cleanup_service.prune_stock_history(db, settings.max_log_entries, settings.max_retention_days)
    except Exception as exc:
        print(f"Error pruning stock history: {exc}")

    db.commit()
    db.refresh(product)
    return product


@router.get("/programs", response_model=List[schemas_stock.ProgramStockSummary])
def get_programs_stock_summary(db: Session = Depends(get_db)):
    ensure_product_columns(db)
    results = db.query(
        models.MiniProgram.program_id,
        models.MiniProgram.program_name,
        func.count(models.Product.id).label("product_count"),
        func.sum(models.Product.stock).label("total_stock"),
    ).outerjoin(
        models.Product,
        and_(
            models.MiniProgram.program_id == models.Product.program_id,
            visible_product_filter(),
        ),
    ).group_by(
        models.MiniProgram.program_id,
        models.MiniProgram.program_name,
    ).order_by(
        desc(models.MiniProgram.sort_order),
        desc("total_stock"),
    ).all()

    summary_list = []
    for item in results:
        summary_list.append({
            "program_id": item.program_id,
            "program_name": item.program_name or "Unknown",
            "product_count": item.product_count,
            "total_stock": item.total_stock or 0,
        })
    return summary_list


@router.get("/center")
def get_stock_center(
    page: int = Query(default=1, ge=1, le=100000),
    size: int = Query(default=20, ge=1, le=100),
    q: Optional[str] = Query(default=None, max_length=100),
    tag: Optional[str] = Query(default=None, max_length=50),
    status: str = Query(default="all"),
    price_mode: str = Query(default="all"),
    cash_max: Optional[float] = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    request: Request = None,
    response: Response = None,
):
    """Return a filtered page of stock items instead of the whole catalog."""
    ensure_product_columns(db)
    cleanup_service.ensure_points_history_columns(db)
    ensure_indexes(db)

    allowed_statuses = {"all", "in_stock", "out_of_stock", "redeemable"}
    allowed_price_modes = {"all", "points_only", "points_plus_cash"}
    if status not in allowed_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid stock status: {status}")
    if price_mode not in allowed_price_modes:
        raise HTTPException(status_code=422, detail=f"Invalid price mode: {price_mode}")

    keyword = (q or "").strip()
    selected_tag = (tag or "").strip()

    cache_key = _stock_center_cache_key(
        page=page,
        size=size,
        keyword=keyword,
        selected_tag=selected_tag,
        status=status,
        price_mode=price_mode,
        cash_max=cash_max,
    )
    revision = _ensure_stock_center_revision(db)
    etag = _build_stock_center_etag(revision, cache_key) if revision is not None else None
    if etag is not None and _if_none_match_matches(request, etag):
        return Response(status_code=304, headers=_stock_center_headers(etag))

    latest_points_subquery = db.query(
        models.PointsHistory.program_id.label("program_id"),
        models.PointsHistory.wechat_id.label("wechat_id"),
        func.max(models.PointsHistory.report_time).label("max_time"),
    ).group_by(
        models.PointsHistory.program_id,
        models.PointsHistory.wechat_id,
    ).subquery()

    max_points_subquery = db.query(
        models.PointsHistory.program_id,
        func.max(models.PointsHistory.points).label("max_user_points"),
        func.max(models.PointsHistory.cash).label("max_user_cash"),
    ).join(
        latest_points_subquery,
        and_(
            models.PointsHistory.program_id == latest_points_subquery.c.program_id,
            models.PointsHistory.wechat_id == latest_points_subquery.c.wechat_id,
            models.PointsHistory.report_time == latest_points_subquery.c.max_time,
        ),
    ).group_by(models.PointsHistory.program_id).subquery()

    points_expr = func.coalesce(models.Product.points, 0)
    cash_expr = func.coalesce(models.Product.cash, 0)
    stock_expr = func.coalesce(models.Product.stock, 0)
    max_points_expr = func.coalesce(max_points_subquery.c.max_user_points, 0)
    max_cash_expr = max_points_subquery.c.max_user_cash
    in_stock_expr = case((stock_expr > 0, 1), else_=0)
    redeemable_expr = case(
        (
            and_(
                stock_expr > 0,
                max_points_expr >= points_expr,
                or_(cash_expr <= 0, and_(max_cash_expr.isnot(None), max_cash_expr >= cash_expr)),
            ),
            1,
        ),
        else_=0,
    )

    tag_program_ids = None
    if selected_tag:
        tag_rows = db.query(models.MiniProgram).all()
        tag_program_ids = [row.program_id for row in tag_rows if selected_tag in get_program_tags(row)]

    def add_filters(query):
        query = query.filter(visible_product_filter())
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(or_(
                models.Product.product_name.ilike(pattern),
                models.Product.product_id.ilike(pattern),
                models.Product.program_id.ilike(pattern),
                models.MiniProgram.program_name.ilike(pattern),
            ))
        if tag_program_ids is not None:
            if tag_program_ids:
                query = query.filter(models.Product.program_id.in_(tag_program_ids))
            else:
                query = query.filter(models.Product.id == -1)
        if status == "in_stock":
            query = query.filter(stock_expr > 0)
        elif status == "out_of_stock":
            query = query.filter(stock_expr <= 0)
        elif status == "redeemable":
            query = query.filter(redeemable_expr == 1)
        if price_mode == "points_only":
            query = query.filter(cash_expr <= 0)
        elif price_mode == "points_plus_cash":
            query = query.filter(cash_expr > 0)
            if cash_max is not None:
                query = query.filter(cash_expr <= cash_max)
        return query

    base_query = db.query(
        models.Product,
        models.MiniProgram.program_name.label("program_name"),
        models.MiniProgram.tags.label("program_tags"),
        max_points_expr.label("max_user_points"),
        max_cash_expr.label("max_user_cash"),
    ).select_from(models.Product).outerjoin(
        models.MiniProgram,
        models.MiniProgram.program_id == models.Product.program_id,
    ).outerjoin(
        max_points_subquery,
        max_points_subquery.c.program_id == models.Product.program_id,
    )
    filtered_query = add_filters(base_query)
    total = int(filtered_query.with_entities(func.count(models.Product.id)).scalar() or 0)

    rows = filtered_query.order_by(
        desc(redeemable_expr),
        desc(in_stock_expr),
        models.Product.product_name.asc(),
        models.Product.id.asc(),
    ).offset((page - 1) * size).limit(size).all()

    items = []
    for product, program_name, raw_tags, max_user_points, max_user_cash in rows:
        items.append({
            "id": product.id,
            "program_id": product.program_id,
            "program_name": program_name or product.program_id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "image_local_path": product.image_local_path,
            "image_url": normalize_stock_image_url(product),
            "points": product.points or 0,
            "cash": float(product.cash or 0),
            "stock": product.stock,
            "max_user_points": float(max_user_points or 0),
            "max_user_cash": float(max_user_cash) if max_user_cash is not None else None,
            "tags": normalize_program_tags(raw_tags),
        })

    summary_query = db.query(
        func.count(models.Product.id),
        func.coalesce(func.sum(case((stock_expr > 0, 1), else_=0)), 0),
        func.coalesce(func.sum(case((stock_expr <= 0, 1), else_=0)), 0),
        func.coalesce(func.sum(redeemable_expr), 0),
        func.coalesce(func.sum(case((cash_expr <= 0, 1), else_=0)), 0),
        func.coalesce(func.sum(case((cash_expr > 0, 1), else_=0)), 0),
    ).select_from(models.Product).outerjoin(
        max_points_subquery,
        max_points_subquery.c.program_id == models.Product.program_id,
    ).filter(visible_product_filter()).one()

    visibility_counts = db.query(
        func.coalesce(func.sum(case((models.Product.is_hidden == 1, 1), else_=0)), 0),
        func.coalesce(func.sum(case((models.Product.is_unlisted == 1, 1), else_=0)), 0),
    ).select_from(models.Product).one()

    payload = {
        "page": page,
        "size": size,
        "total": total,
        "items": items,
        "summary": {
            "totalProducts": int(summary_query[0] or 0),
            "inStockProducts": int(summary_query[1] or 0),
            "outOfStockProducts": int(summary_query[2] or 0),
            "redeemableProducts": int(summary_query[3] or 0),
            "pointsOnlyProducts": int(summary_query[4] or 0),
            "mixedProducts": int(summary_query[5] or 0),
        },
        "available_tags": get_all_distinct_tags(db),
        "hidden_total": int(visibility_counts[0] or 0),
        "off_shelf_total": int(visibility_counts[1] or 0),
    }

    # SQLite uses the durable trigger-backed revision above, so a matching
    # request can exit before running the expensive catalog queries.  If a
    # different backend (or a temporary SQLite setup failure) reaches this
    # branch, hash the exact response instead of returning a potentially stale
    # 304 based on an approximate aggregate.
    if etag is None:
        etag = _build_stock_center_body_etag(payload, cache_key)
        if _if_none_match_matches(request, etag):
            return Response(status_code=304, headers=_stock_center_headers(etag))

    if response is not None:
        response.headers.update(_stock_center_headers(etag))
    return payload


@router.get("/programs/{program_id}/products", response_model=schemas_stock.PaginatedProducts)
def get_program_products(
    program_id: str,
    page: int = 1,
    size: int = 20,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ensure_product_columns(db)
    query = db.query(models.Product).filter(models.Product.program_id == program_id, visible_product_filter())
    if q:
        query = query.filter(models.Product.product_name.contains(q))

    total = query.count()
    items = query.order_by(models.Product.points.asc(), models.Product.id.asc()).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/search", response_model=schemas_stock.PaginatedProducts)
def search_products_global(
    q: str = Query(..., min_length=1),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    ensure_product_columns(db)
    query = db.query(models.Product).filter(visible_product_filter(), models.Product.product_name.contains(q))
    total = query.count()
    items = query.order_by(models.Product.points.asc(), models.Product.id.asc()).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/hidden", response_model=schemas_stock.PaginatedProducts)
def get_hidden_products(
    page: int = 1,
    size: int = 20,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ensure_product_columns(db)
    query = db.query(models.Product).filter(hidden_product_filter())
    if q:
        query = query.filter(models.Product.product_name.contains(q))

    total = query.count()
    items = query.order_by(models.Product.hidden_at.desc(), models.Product.id.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get("/off-shelf")
def get_off_shelf_products(
    page: int = Query(default=1, ge=1, le=100000),
    size: int = Query(default=50, ge=1, le=100),
    q: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    """已下架（unlisted）商品 — 系统在处理 stock 上报时检测到老商品没出现在最新报告里，
    自动标记为 is_unlisted=1。和「已隐藏」（is_hidden，用户手动）完全独立。"""
    ensure_product_columns(db)

    keyword = (q or "").strip()
    query = db.query(models.Product).outerjoin(
        models.MiniProgram,
        models.MiniProgram.program_id == models.Product.program_id,
    ).filter(unlisted_product_filter())
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(or_(
            models.Product.product_name.ilike(pattern),
            models.Product.product_id.ilike(pattern),
            models.Product.program_id.ilike(pattern),
            models.MiniProgram.program_name.ilike(pattern),
        ))

    total = int(query.with_entities(func.count(models.Product.id)).scalar() or 0)
    group_count_rows = query.with_entities(
        models.Product.program_id,
        func.count(models.Product.id),
    ).group_by(models.Product.program_id).all()
    group_total_map = {row[0]: int(row[1] or 0) for row in group_count_rows}

    products = query.with_entities(models.Product).order_by(
        models.Product.unlisted_at.desc(),
        models.Product.id.desc(),
    ).offset((page - 1) * size).limit(size).all()

    program_ids = {product.program_id for product in products if product.program_id}
    program_map = {}
    if program_ids:
        program_rows = db.query(
            models.MiniProgram.program_id,
            models.MiniProgram.program_name,
        ).filter(models.MiniProgram.program_id.in_(program_ids)).all()
        program_map = {row.program_id: row.program_name for row in program_rows}

    grouped = {}
    for product in products:
        program_name = program_map.get(product.program_id) or product.program_id
        bucket = grouped.setdefault(product.program_id, {
            "program_id": product.program_id,
            "program_name": program_name,
            "products": [],
        })
        bucket["products"].append({
            "id": product.id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "points": product.points or 0,
            "cash": float(product.cash or 0),
            "stock": product.stock,
            "image_url": normalize_stock_image_url(product),
            "unlisted_at": product.unlisted_at.isoformat() if product.unlisted_at else None,
        })

    off_shelf_groups = []
    for program_id, group in grouped.items():
        group["count"] = len(group["products"])
        group["total_count"] = group_total_map.get(program_id, group["count"])
        off_shelf_groups.append(group)

    off_shelf_groups.sort(key=lambda item: (-item["count"], item["program_name"] or item["program_id"]))
    return {
        "page": page,
        "size": size,
        "total": total,
        "program_count": len(off_shelf_groups),
        "items": off_shelf_groups,
    }


@router.put("/products/{product_id}/hide")
def hide_product(product_id: int, db: Session = Depends(get_db)):
    ensure_product_columns(db)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_hidden = 1
    product.hidden_at = datetime.utcnow()
    db.commit()
    return {
        "status": "success",
        "id": product.id,
        "is_hidden": True,
    }


@router.put("/products/{product_id}/restore")
def restore_product(product_id: int, db: Session = Depends(get_db)):
    ensure_product_columns(db)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_hidden = 0
    product.hidden_at = None
    db.commit()
    return {
        "status": "success",
        "id": product.id,
        "is_hidden": False,
    }


@router.put("/products/{product_id}/relist")
def relist_product(product_id: int, db: Session = Depends(get_db)):
    """把系统判定为「已下架」的商品手动恢复为活跃状态。和 /restore（取消手动隐藏）独立。"""
    ensure_product_columns(db)
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_unlisted = 0
    product.unlisted_at = None
    db.commit()
    return {
        "status": "success",
        "id": product.id,
        "is_unlisted": False,
    }
