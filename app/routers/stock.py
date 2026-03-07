from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session

from app import models, schemas_stock
from app.database import get_db
from app.services import cleanup_service

router = APIRouter(prefix="/api/v1/stock", tags=["stock-management"])


def ensure_product_columns(db: Session):
    expected_columns = {
        "is_hidden": "ALTER TABLE products ADD COLUMN is_hidden INTEGER DEFAULT 0",
        "hidden_at": "ALTER TABLE products ADD COLUMN hidden_at DATETIME",
    }

    connection = db.bind.connect()
    try:
        inspector = db.bind.dialect.get_columns(connection, "products")
        column_names = {column["name"] for column in inspector}
    finally:
        connection.close()

    missing_statements = [
        statement
        for column_name, statement in expected_columns.items()
        if column_name not in column_names
    ]
    if not missing_statements:
        return

    for statement in missing_statements:
        db.execute(text(statement))
    db.commit()



def visible_product_filter():
    return or_(models.Product.is_hidden == 0, models.Product.is_hidden.is_(None))



def hidden_product_filter():
    return models.Product.is_hidden == 1



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
def get_stock_center(db: Session = Depends(get_db)):
    ensure_product_columns(db)
    latest_points_subquery = db.query(
        models.PointsHistory.program_id.label("program_id"),
        models.PointsHistory.wechat_id.label("wechat_id"),
        func.max(models.PointsHistory.report_time).label("max_time"),
    ).group_by(
        models.PointsHistory.program_id,
        models.PointsHistory.wechat_id,
    ).subquery()

    max_points_rows = db.query(
        models.PointsHistory.program_id,
        func.max(models.PointsHistory.points).label("max_user_points"),
    ).join(
        latest_points_subquery,
        and_(
            models.PointsHistory.program_id == latest_points_subquery.c.program_id,
            models.PointsHistory.wechat_id == latest_points_subquery.c.wechat_id,
            models.PointsHistory.report_time == latest_points_subquery.c.max_time,
        ),
    ).group_by(models.PointsHistory.program_id).all()
    max_points_map = {row.program_id: int(row.max_user_points or 0) for row in max_points_rows}

    program_rows = db.query(
        models.MiniProgram.program_id,
        models.MiniProgram.program_name,
        models.MiniProgram.sort_order,
    ).order_by(
        desc(models.MiniProgram.sort_order),
        models.MiniProgram.id.asc(),
    ).all()
    program_map = {
        row.program_id: {
            "program_id": row.program_id,
            "program_name": row.program_name or row.program_id,
            "max_user_points": max_points_map.get(row.program_id, 0),
        }
        for row in program_rows
    }

    products = db.query(models.Product).filter(visible_product_filter()).order_by(
        models.Product.points.asc(),
        models.Product.id.asc(),
    ).all()

    items = []
    for product in products:
        program_info = program_map.get(product.program_id, {
            "program_id": product.program_id,
            "program_name": product.program_id,
            "max_user_points": max_points_map.get(product.program_id, 0),
        })
        items.append({
            "id": product.id,
            "program_id": product.program_id,
            "program_name": program_info["program_name"],
            "product_id": product.product_id,
            "product_name": product.product_name,
            "image_local_path": product.image_local_path,
            "image_url": normalize_stock_image_url(product),
            "points": product.points,
            "stock": product.stock,
            "max_user_points": program_info["max_user_points"],
        })

    programs = []
    for program in program_map.values():
        products_for_program = [item for item in items if item["program_id"] == program["program_id"]]
        programs.append({
            **program,
            "product_count": len(products_for_program),
            "total_stock": sum(int(item["stock"] or 0) for item in products_for_program),
        })

    return {
        "programs": programs,
        "items": items,
    }


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
