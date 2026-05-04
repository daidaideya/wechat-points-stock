from collections import defaultdict
from datetime import datetime, timedelta
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pypinyin import Style, lazy_pinyin, pinyin
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services import cleanup_service

router = APIRouter(tags=["api"])


class AccountUpdate(BaseModel):
    nickname: Optional[str] = None
    device: Optional[str] = None
    phone: Optional[str] = None


class SortOrderUpdate(BaseModel):
    wechat_ids: List[str]


class LogSettingsUpdate(BaseModel):
    max_log_entries: int
    max_retention_days: int
    access_protection_enabled: bool = False
    access_key: Optional[str] = None


class AccessVerifyRequest(BaseModel):
    access_key: str


class ProgramUpdate(BaseModel):
    auth_type: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    note: Optional[str] = None
    tags: Optional[List[str]] = None
    is_archived: Optional[bool] = None


def get_program_pinyin_data(program_name: Optional[str]):
    if not program_name:
        return "", ""
    full_pinyin = "".join(lazy_pinyin(program_name))
    first_letters = "".join([p[0][0] for p in pinyin(program_name, style=Style.FIRST_LETTER)])
    return full_pinyin, first_letters


def normalize_program_tags(tags_input) -> List[str]:
    if tags_input is None:
        return []

    if isinstance(tags_input, list):
        raw_tags = tags_input
    else:
        raw_value = str(tags_input).strip()
        if not raw_value:
            return []

        raw_tags = None
        if raw_value.startswith("["):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    raw_tags = parsed
            except Exception:
                raw_tags = None

        if raw_tags is None:
            raw_tags = raw_value.replace("，", ",").split(",")

    cleaned_tags = []
    seen = set()
    for tag in raw_tags:
        text_value = str(tag).strip()
        if not text_value or text_value in seen:
            continue
        seen.add(text_value)
        cleaned_tags.append(text_value[:20])

    return cleaned_tags[:20]


def serialize_program_tags(tags_input) -> Optional[str]:
    tags = normalize_program_tags(tags_input)
    if not tags:
        return None
    return json.dumps(tags, ensure_ascii=False)


def get_program_tags(program) -> List[str]:
    return normalize_program_tags(getattr(program, "tags", None))


def ensure_mini_program_columns(db: Session):
    expected_columns = {
        "auth_type": "ALTER TABLE mini_programs ADD COLUMN auth_type VARCHAR(20) DEFAULT 'code'",
        "sort_order": "ALTER TABLE mini_programs ADD COLUMN sort_order INTEGER DEFAULT 0",
        "is_favorite": "ALTER TABLE mini_programs ADD COLUMN is_favorite INTEGER DEFAULT 0",
        "note": "ALTER TABLE mini_programs ADD COLUMN note VARCHAR",
        "tags": "ALTER TABLE mini_programs ADD COLUMN tags VARCHAR",
        "is_archived": "ALTER TABLE mini_programs ADD COLUMN is_archived INTEGER DEFAULT 0",
        "archived_at": "ALTER TABLE mini_programs ADD COLUMN archived_at DATETIME",
    }

    connection = db.bind.connect()
    try:
        inspector = db.bind.dialect.get_columns(connection, "mini_programs")
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


def ensure_program_tags_column(db: Session):
    ensure_mini_program_columns(db)


_INDEXES_ENSURED = False


def ensure_indexes(db: Session):
    """Create hot-path indexes that SQLite does not auto-create from FK
    declarations. The /points and /accounts endpoints filter PointsHistory
    by wechat_id and order by report_time, both of which scan the whole
    table without these. Runs once per process."""
    global _INDEXES_ENSURED
    if _INDEXES_ENSURED:
        return
    statements = [
        "CREATE INDEX IF NOT EXISTS ix_points_history_wechat_id ON points_history (wechat_id)",
        "CREATE INDEX IF NOT EXISTS ix_points_history_program_id ON points_history (program_id)",
        "CREATE INDEX IF NOT EXISTS ix_points_history_report_time ON points_history (report_time)",
        "CREATE INDEX IF NOT EXISTS ix_points_history_wechat_program ON points_history (wechat_id, program_id)",
        "CREATE INDEX IF NOT EXISTS ix_stock_history_program_id ON stock_history (program_id)",
        "CREATE INDEX IF NOT EXISTS ix_stock_history_change_time ON stock_history (change_time)",
        "CREATE INDEX IF NOT EXISTS ix_products_program_id ON products (program_id)",
    ]
    try:
        for stmt in statements:
            db.execute(text(stmt))
        db.commit()
        _INDEXES_ENSURED = True
    except Exception as exc:
        db.rollback()
        # Don't crash the request if index creation fails; just log and move on.
        print(f"[ensure_indexes] failed: {exc}")


def get_all_distinct_tags(db: Session) -> List[str]:
    rows = db.query(models.MiniProgram.tags).filter(
        models.MiniProgram.tags.isnot(None),
        models.MiniProgram.tags != "",
        or_(models.MiniProgram.is_archived == 0, models.MiniProgram.is_archived.is_(None)),
    ).all()

    tag_counts = {}
    for row in rows:
        for tag in normalize_program_tags(row[0]):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return [
        tag
        for tag, _count in sorted(
            tag_counts.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
    ]


def normalize_image_url(product: models.Product) -> Optional[str]:
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


def get_program_last_updates(db: Session, program_ids: List[str]):
    if not program_ids:
        return {}

    rows = db.query(
        models.PointsHistory.program_id,
        func.max(models.PointsHistory.report_time),
    ).filter(
        models.PointsHistory.program_id.in_(program_ids)
    ).group_by(models.PointsHistory.program_id).all()

    return {row[0]: row[1].isoformat() if row[1] else None for row in rows}


def get_latest_points_records_for_program(db: Session, program_id: str):
    history = db.query(models.PointsHistory).filter(
        models.PointsHistory.program_id == program_id
    ).order_by(models.PointsHistory.report_time.desc()).all()

    user_points_map = {}
    for item in history:
        if item.wechat_id not in user_points_map:
            user_points_map[item.wechat_id] = item
    return user_points_map


def get_program_has_stock_map(db: Session, program_ids: List[str]):
    has_stock_map = {}
    if not program_ids:
        return has_stock_map

    stock_rows = db.query(models.Product.program_id).filter(
        models.Product.program_id.in_(program_ids)
    ).distinct().all()
    has_stock_ids = {row[0] for row in stock_rows}
    for program_id in program_ids:
        has_stock_map[program_id] = program_id in has_stock_ids
    return has_stock_map


def get_program_stock_summary_map(db: Session, program_ids: List[str]):
    if not program_ids:
        return {}

    rows = db.query(
        models.Product.program_id,
        func.count(models.Product.id).label("product_count"),
    ).filter(
        models.Product.program_id.in_(program_ids),
        or_(models.Product.is_hidden == 0, models.Product.is_hidden.is_(None)),
    ).group_by(models.Product.program_id).all()

    summary_map = {program_id: {"product_count": 0} for program_id in program_ids}
    for row in rows:
        summary_map[row.program_id] = {
            "product_count": int(row.product_count or 0),
        }
    return summary_map


def get_program_stock_change_map(db: Session, program_ids: List[str]):
    if not program_ids:
        return {}

    tz_offset = timedelta(hours=8)
    now_cst = datetime.utcnow() + tz_offset
    today_cst = now_cst.date()
    previous_day_cst = today_cst - timedelta(days=1)

    change_map = {
        program_id: {
            "added_count": 0,
            "removed_count": 0,
            "changed": False,
        }
        for program_id in program_ids
    }

    report_rows = db.query(
        models.StockHistory.program_id,
        models.StockHistory.product_id,
        func.max(models.StockHistory.change_time).label("last_change_time"),
    ).filter(
        models.StockHistory.program_id.in_(program_ids),
    ).group_by(
        models.StockHistory.program_id,
        models.StockHistory.product_id,
    ).all()

    latest_report_dates = {}
    for row in report_rows:
        if not row.last_change_time:
            continue
        report_date = (row.last_change_time + tz_offset).date()
        latest_date = latest_report_dates.get(row.program_id)
        if latest_date is None or report_date > latest_date:
            latest_report_dates[row.program_id] = report_date

    previous_report_dates = {program_id: None for program_id in program_ids}
    for row in report_rows:
        if not row.last_change_time:
            continue
        report_date = (row.last_change_time + tz_offset).date()
        latest_date = latest_report_dates.get(row.program_id)
        if latest_date is None or report_date >= latest_date:
            continue
        previous_date = previous_report_dates.get(row.program_id)
        if previous_date is None or report_date > previous_date:
            previous_report_dates[row.program_id] = report_date

    latest_product_ids = defaultdict(set)
    previous_product_ids = defaultdict(set)
    for row in report_rows:
        if not row.last_change_time:
            continue
        report_date = (row.last_change_time + tz_offset).date()
        if report_date == latest_report_dates.get(row.program_id):
            latest_product_ids[row.program_id].add(row.product_id)
        if report_date == previous_report_dates.get(row.program_id):
            previous_product_ids[row.program_id].add(row.product_id)

    for program_id in program_ids:
        latest_ids = latest_product_ids.get(program_id, set())
        previous_ids = previous_product_ids.get(program_id, set())

        if not latest_ids and not previous_ids:
            continue

        added_count = len(latest_ids - previous_ids) if previous_ids else 0
        removed_count = len(previous_ids - latest_ids) if previous_ids else 0

        latest_date = latest_report_dates.get(program_id)
        should_show = latest_date == today_cst or latest_date == previous_day_cst

        change_map[program_id] = {
            "added_count": added_count if should_show else 0,
            "removed_count": removed_count if should_show else 0,
            "changed": should_show and (added_count > 0 or removed_count > 0),
        }

    return change_map


def build_program_payload(program, last_updates, has_stock_map, stock_summary_map=None, stock_change_map=None):
    stock_summary = (stock_summary_map or {}).get(program.program_id, {})
    stock_change = (stock_change_map or {}).get(program.program_id, {})
    return {
        "id": program.id,
        "program_id": program.program_id,
        "program_name": program.program_name,
        "auth_type": program.auth_type,
        "sort_order": program.sort_order,
        "is_favorite": program.is_favorite == 1,
        "last_update_time": last_updates.get(program.program_id),
        "has_stock": has_stock_map.get(program.program_id, False),
        "product_count": int(stock_summary.get("product_count", 0)),
        "stock_change": {
            "added_count": int(stock_change.get("added_count", 0)),
            "removed_count": int(stock_change.get("removed_count", 0)),
            "changed": bool(stock_change.get("changed", False)),
        },
        "note": program.note,
        "tags": get_program_tags(program),
        "is_archived": getattr(program, "is_archived", 0) == 1,
        "archived_at": program.archived_at.isoformat() if getattr(program, "archived_at", None) else None,
    }


def verify_access_or_raise(
    db: Session,
    x_access_key: Optional[str],
    allow_empty_when_disabled: bool = True,
):
    settings = cleanup_service.get_or_create_settings(db)
    enabled = settings.access_protection_enabled == 1
    stored_key = (settings.access_key or "").strip()

    if not enabled:
        return settings

    if not stored_key:
        if allow_empty_when_disabled:
            return settings
        raise HTTPException(status_code=403, detail="已开启访问保护，但尚未设置访问密钥")

    if (x_access_key or "").strip() != stored_key:
        raise HTTPException(status_code=401, detail="访问密钥错误或未提供")

    return settings


def fetch_points_history_grouped(db: Session, wechat_ids):
    """One-shot pull of all PointsHistory rows for a set of wechat_ids,
    grouped per wechat_id, descending by report_time. Avoids the N+1
    pattern where each account triggers its own history query."""
    if not wechat_ids:
        return {}
    rows = db.query(models.PointsHistory).filter(
        models.PointsHistory.wechat_id.in_(wechat_ids)
    ).order_by(models.PointsHistory.report_time.desc()).all()
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.wechat_id].append(row)
    return grouped


def get_archived_program_ids(db: Session):
    return {
        row[0]
        for row in db.query(models.MiniProgram.program_id).filter(
            models.MiniProgram.is_archived == 1
        ).all()
    }


def build_account_points_summary(
    db: Session,
    account: models.WechatAccount,
    all_programs,
    archived_program_ids: Optional[set] = None,
    program_name_map: Optional[dict] = None,
    user_points=None,
):
    archived_program_ids = archived_program_ids or set()
    if program_name_map is None:
        program_name_map = {p.program_id: p.program_name for p in all_programs}

    if user_points is None:
        user_points = db.query(models.PointsHistory).filter(
            models.PointsHistory.wechat_id == account.wechat_id
        ).order_by(models.PointsHistory.report_time.desc()).all()

    latest_map = {}
    history_map = defaultdict(list)
    for item in user_points:
        history_map[item.program_id].append(item)
        if item.program_id not in latest_map:
            latest_map[item.program_id] = item

    tz_offset = timedelta(hours=8)
    now_cst = datetime.utcnow() + tz_offset
    today_cst_date = now_cst.date()

    def calculate_diff(program_id, current_points):
        if current_points == "未注册":
            return 0

        records = history_map.get(program_id, [])
        if not records:
            return 0

        latest = records[0]
        latest_cst = (latest.report_time or datetime.utcnow()) + tz_offset
        if latest_cst.date() != today_cst_date:
            return 0

        prev_points = 0
        for record in records[1:]:
            record_cst = (record.report_time or datetime.utcnow()) + tz_offset
            if record_cst.date() < today_cst_date:
                prev_points = record.points
                break
        return current_points - prev_points

    def resolve_name(program_id):
        return program_name_map.get(program_id) or program_id

    points_items = []
    processed_program_ids = set()
    active_program_count = 0

    for program in all_programs:
        processed_program_ids.add(program.program_id)
        if program.program_id in latest_map:
            current = latest_map[program.program_id]
            if current.points != 0:
                active_program_count += 1
            points_items.append({
                "program_id": current.program_id,
                "program_name": resolve_name(current.program_id),
                "points": current.points,
                "diff": calculate_diff(current.program_id, current.points),
                "report_time": current.report_time.isoformat() if current.report_time else None,
            })
        else:
            points_items.append({
                "program_id": program.program_id,
                "program_name": program.program_name or program.program_id,
                "points": "未注册",
                "diff": 0,
                "report_time": None,
            })

    for program_id, current in latest_map.items():
        if program_id in processed_program_ids:
            continue
        if program_id in archived_program_ids:
            continue
        if current.points != 0:
            active_program_count += 1
        points_items.append({
            "program_id": current.program_id,
            "program_name": resolve_name(current.program_id),
            "points": current.points,
            "diff": calculate_diff(current.program_id, current.points),
            "report_time": current.report_time.isoformat() if current.report_time else None,
        })

    def sort_key(item):
        points_value = item["points"]
        if points_value == "未注册":
            return (0, 0)
        if points_value == 0:
            return (1, 0)
        return (2, -points_value)

    points_items.sort(key=sort_key)
    return {
        "account": {
            "wechat_id": account.wechat_id,
            "nickname": account.nickname,
            "device": account.device,
            "phone": account.phone,
            "sort_order": account.sort_order,
        },
        "active_program_count": active_program_count,
        "points": points_items,
    }


@router.get("/api/v1/dashboard")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    ensure_indexes(db)
    account_count = db.query(models.WechatAccount).count()
    program_count = db.query(models.MiniProgram).count()
    points_records_count = db.query(models.PointsHistory).count()
    total_products_count = db.query(models.Product).count()
    out_of_stock_count = db.query(models.Product).filter(models.Product.stock == 0).count()
    favorite_count = db.query(models.MiniProgram).filter(models.MiniProgram.is_favorite == 1).count()
    token_auth_count = db.query(models.MiniProgram).filter(models.MiniProgram.auth_type == "token").count()
    cached_images_count = db.query(models.Product).filter(models.Product.image_local_path.isnot(None)).count()
    archived_count = db.query(models.MiniProgram).filter(models.MiniProgram.is_archived == 1).count()

    programs = db.query(models.MiniProgram).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    today_str = datetime.now().strftime("%Y-%m-%d")

    archived_program_ids = {p.program_id for p in programs if (p.is_archived or 0) == 1}
    active_programs = [p for p in programs if p.program_id not in archived_program_ids]
    active_program_ids = [p.program_id for p in active_programs]

    unreported_programs = []
    for program in active_programs:
        last_time_iso = last_updates.get(program.program_id)
        if not last_time_iso or last_time_iso.split("T")[0] != today_str:
            unreported_programs.append((program, last_time_iso))
    unreported_count = len(unreported_programs)

    has_stock_map = get_program_has_stock_map(db, active_program_ids)
    stock_summary_map = get_program_stock_summary_map(db, active_program_ids)
    stock_change_map = get_program_stock_change_map(db, active_program_ids)
    unreported_top = []
    for program, last_time_iso in unreported_programs[:5]:
        payload = build_program_payload(program, last_updates, has_stock_map, stock_summary_map, stock_change_map)
        payload["last_report_time"] = last_time_iso
        unreported_top.append(payload)

    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc = start_of_day - timedelta(hours=8)
    active_accounts_today = db.query(models.PointsHistory.wechat_id).filter(
        models.PointsHistory.report_time >= start_of_day_utc
    ).distinct().count()

    raw_history = db.query(models.PointsHistory).order_by(models.PointsHistory.report_time.desc()).limit(50).all()
    program_name_map = {p.program_id: p.program_name for p in programs}
    recent_program_updates = []
    seen_programs = set()
    for item in raw_history:
        if item.program_id in seen_programs:
            continue
        if item.program_id in archived_program_ids:
            continue
        recent_program_updates.append({
            "program_id": item.program_id,
            "program_name": program_name_map.get(item.program_id) or item.program_id,
            "wechat_id": item.wechat_id,
            "points": item.points,
            "report_time": item.report_time.isoformat() if item.report_time else None,
        })
        seen_programs.add(item.program_id)
        if len(recent_program_updates) >= 5:
            break

    return {
        "account_count": account_count,
        "program_count": program_count,
        "unreported_count": unreported_count,
        "points_records_count": points_records_count,
        "total_products_count": total_products_count,
        "out_of_stock_count": out_of_stock_count,
        "favorite_count": favorite_count,
        "token_auth_count": token_auth_count,
        "cached_images_count": cached_images_count,
        "active_accounts_today": active_accounts_today,
        "archived_count": archived_count,
        "recent_program_updates": recent_program_updates,
        "unreported_top": unreported_top,
    }


@router.get("/api/v1/access/status")
async def get_access_status(
    x_access_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    settings = cleanup_service.get_or_create_settings(db)
    enabled = settings.access_protection_enabled == 1
    has_access_key = bool((settings.access_key or "").strip())

    if enabled and has_access_key:
        verify_access_or_raise(db, x_access_key, allow_empty_when_disabled=False)

    return {
        "enabled": enabled and has_access_key,
        "configured": has_access_key,
    }


@router.post("/api/v1/access/verify")
async def verify_access_key(payload: AccessVerifyRequest, db: Session = Depends(get_db)):
    settings = cleanup_service.get_or_create_settings(db)
    enabled = settings.access_protection_enabled == 1
    stored_key = (settings.access_key or "").strip()

    if not enabled or not stored_key:
        return JSONResponse(content={"status": "disabled"})

    if payload.access_key.strip() != stored_key:
        raise HTTPException(status_code=401, detail="访问密钥错误")

    return JSONResponse(content={"status": "success"})


@router.get("/api/v1/settings/logs")
async def get_log_settings(
    x_access_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    settings = cleanup_service.get_or_create_settings(db)
    if settings.access_protection_enabled == 1 and (settings.access_key or "").strip():
        verify_access_or_raise(db, x_access_key, allow_empty_when_disabled=False)
    return {
        "max_log_entries": settings.max_log_entries,
        "max_retention_days": settings.max_retention_days,
        "access_protection_enabled": settings.access_protection_enabled == 1,
        "access_key_configured": bool((settings.access_key or "").strip()),
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
    }


@router.post("/api/v1/settings/logs")
async def update_log_settings(
    update: LogSettingsUpdate,
    x_access_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    settings = cleanup_service.get_or_create_settings(db)
    if settings.access_protection_enabled == 1 and (settings.access_key or "").strip():
        verify_access_or_raise(db, x_access_key, allow_empty_when_disabled=False)
    settings.max_log_entries = max(0, update.max_log_entries)
    settings.max_retention_days = max(0, update.max_retention_days)
    settings.access_protection_enabled = 1 if update.access_protection_enabled else 0

    if update.access_key is not None:
        normalized_key = update.access_key.strip()
        settings.access_key = normalized_key or None

    settings.updated_at = datetime.utcnow()
    db.add(settings)
    cleanup_service.prune_points_history(db, settings.max_log_entries, settings.max_retention_days)
    cleanup_service.prune_stock_history(db, settings.max_log_entries, settings.max_retention_days)
    db.commit()
    return JSONResponse(content={"status": "success"})


@router.get("/api/v1/accounts")
async def get_accounts(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    ensure_indexes(db)
    accounts = db.query(models.WechatAccount).order_by(
        models.WechatAccount.sort_order.asc(),
        models.WechatAccount.id.asc(),
    ).all()
    all_programs_full = db.query(models.MiniProgram).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    archived_ids = {p.program_id for p in all_programs_full if (p.is_archived or 0) == 1}
    all_programs = [p for p in all_programs_full if p.program_id not in archived_ids]
    program_name_map = {p.program_id: p.program_name for p in all_programs_full}

    history_grouped = fetch_points_history_grouped(db, [a.wechat_id for a in accounts])

    items = []
    for account in accounts:
        summary = build_account_points_summary(
            db,
            account,
            all_programs,
            archived_program_ids=archived_ids,
            program_name_map=program_name_map,
            user_points=history_grouped.get(account.wechat_id, []),
        )
        items.append({
            **summary["account"],
            "active_program_count": summary["active_program_count"],
        })
    return {"items": items}


@router.get("/api/v1/accounts/{wechat_id}")
async def get_account(wechat_id: str, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    ensure_indexes(db)
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    all_programs_full = db.query(models.MiniProgram).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    archived_ids = {p.program_id for p in all_programs_full if (p.is_archived or 0) == 1}
    all_programs = [p for p in all_programs_full if p.program_id not in archived_ids]
    program_name_map = {p.program_id: p.program_name for p in all_programs_full}
    return build_account_points_summary(
        db,
        account,
        all_programs,
        archived_program_ids=archived_ids,
        program_name_map=program_name_map,
    )


@router.get("/api/v1/accounts/{wechat_id}/points_details")
async def get_account_points_details(wechat_id: str, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    ensure_indexes(db)
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    all_programs_full = db.query(models.MiniProgram).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    archived_ids = {p.program_id for p in all_programs_full if (p.is_archived or 0) == 1}
    all_programs = [p for p in all_programs_full if p.program_id not in archived_ids]
    program_name_map = {p.program_id: p.program_name for p in all_programs_full}
    return build_account_points_summary(
        db,
        account,
        all_programs,
        archived_program_ids=archived_ids,
        program_name_map=program_name_map,
    )["points"]


@router.put("/api/v1/accounts/sort-order")
async def update_sort_order(update: SortOrderUpdate, db: Session = Depends(get_db)):
    for index, wechat_id in enumerate(update.wechat_ids):
        account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
        if account:
            account.sort_order = index
            db.add(account)
    db.commit()
    return JSONResponse(content={"status": "success"})


@router.put("/api/v1/accounts/{wechat_id}")
async def update_account(wechat_id: str, update: AccountUpdate, db: Session = Depends(get_db)):
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        account = models.WechatAccount(
            wechat_id=wechat_id,
            nickname=update.nickname,
            device=update.device,
            phone=update.phone,
        )
        db.add(account)
    else:
        if update.nickname is not None:
            account.nickname = update.nickname
        if update.device is not None:
            account.device = update.device
        if update.phone is not None:
            account.phone = update.phone
        db.add(account)

    db.commit()
    return JSONResponse(content={"status": "success"})


@router.delete("/api/v1/accounts/{wechat_id}")
async def delete_account(wechat_id: str, db: Session = Depends(get_db)):
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.query(models.PointsHistory).filter(models.PointsHistory.wechat_id == wechat_id).delete()
    db.delete(account)
    db.commit()
    return JSONResponse(content={"status": "success"})


@router.delete("/api/v1/accounts/{wechat_id}/programs/{program_id}")
async def delete_program_points(wechat_id: str, program_id: str, db: Session = Depends(get_db)):
    deleted_count = db.query(models.PointsHistory).filter(
        models.PointsHistory.wechat_id == wechat_id,
        models.PointsHistory.program_id == program_id,
    ).delete()
    db.commit()
    return JSONResponse(content={"status": "success", "deleted_count": deleted_count})


@router.get("/api/v1/points")
async def get_points_overview(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    ensure_indexes(db)
    accounts = db.query(models.WechatAccount).order_by(
        models.WechatAccount.sort_order.asc(),
        models.WechatAccount.id.asc(),
    ).all()
    all_programs_full = db.query(models.MiniProgram).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    archived_ids = {p.program_id for p in all_programs_full if (p.is_archived or 0) == 1}
    all_programs = [p for p in all_programs_full if p.program_id not in archived_ids]
    program_name_map = {p.program_id: p.program_name for p in all_programs_full}

    history_grouped = fetch_points_history_grouped(db, [a.wechat_id for a in accounts])

    items = []
    for account in accounts:
        summary = build_account_points_summary(
            db,
            account,
            all_programs,
            archived_program_ids=archived_ids,
            program_name_map=program_name_map,
            user_points=history_grouped.get(account.wechat_id, []),
        )
        items.append({
            "account": summary["account"],
            "active_program_count": summary["active_program_count"],
            "points": summary["points"],
        })
    return {"items": items}


@router.get("/api/v1/programs")
async def get_programs_api(
    page: int = 1,
    size: int = 21,
    q: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    tag: Optional[str] = None,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
):
    ensure_mini_program_columns(db)
    query = db.query(models.MiniProgram)
    programs = []
    total = 0

    normalized_status = (status or "active").strip().lower()
    if normalized_status not in {"active", "archived", "all"}:
        normalized_status = "active"
    if normalized_status == "active":
        query = query.filter(or_(models.MiniProgram.is_archived == 0, models.MiniProgram.is_archived.is_(None)))
    elif normalized_status == "archived":
        query = query.filter(models.MiniProgram.is_archived == 1)

    if is_favorite is not None:
        if is_favorite:
            query = query.filter(models.MiniProgram.is_favorite == 1)
        else:
            query = query.filter(or_(models.MiniProgram.is_favorite == 0, models.MiniProgram.is_favorite.is_(None)))

    normalized_tag = (tag or "").strip()
    if normalized_tag:
        query = query.filter(models.MiniProgram.tags.isnot(None)).filter(
            or_(
                models.MiniProgram.tags == json.dumps([normalized_tag], ensure_ascii=False),
                models.MiniProgram.tags.like(f'%"{normalized_tag}"%'),
            )
        )

    if q:
        total_count = query.count()
        if total_count < 2000:
            all_programs = query.order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()
            filtered_programs = []
            q_lower = q.lower()
            for program in all_programs:
                if (program.program_name and q in program.program_name) or (q in program.program_id.lower()):
                    filtered_programs.append(program)
                    continue
                if program.program_name:
                    full_pinyin, first_letters = get_program_pinyin_data(program.program_name)
                    if q_lower in full_pinyin or q_lower in first_letters:
                        filtered_programs.append(program)
            total = len(filtered_programs)
            start = (page - 1) * size
            end = start + size
            programs = filtered_programs[start:end]
        else:
            query = query.filter(or_(
                models.MiniProgram.program_name.contains(q),
                models.MiniProgram.program_id.contains(q),
            ))
            query = query.order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc())
            total = query.count()
            programs = query.offset((page - 1) * size).limit(size).all()
    else:
        query = query.order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc())
        total = query.count()
        programs = query.offset((page - 1) * size).limit(size).all()

    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    has_stock_map = get_program_has_stock_map(db, program_ids)
    stock_summary_map = get_program_stock_summary_map(db, program_ids)
    stock_change_map = get_program_stock_change_map(db, program_ids)
    items = [build_program_payload(program, last_updates, has_stock_map, stock_summary_map, stock_change_map) for program in programs]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "has_more": (page * size) < total,
        "available_tags": get_all_distinct_tags(db),
        "current_tag": normalized_tag or None,
        "status": normalized_status,
    }


@router.get("/api/v1/programs/favorites")
async def get_favorite_programs(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    programs = db.query(models.MiniProgram).filter(
        models.MiniProgram.is_favorite == 1,
        or_(models.MiniProgram.is_archived == 0, models.MiniProgram.is_archived.is_(None)),
    ).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    has_stock_map = get_program_has_stock_map(db, program_ids)
    stock_summary_map = get_program_stock_summary_map(db, program_ids)
    stock_change_map = get_program_stock_change_map(db, program_ids)
    return {
        "items": [build_program_payload(program, last_updates, has_stock_map, stock_summary_map, stock_change_map) for program in programs]
    }


@router.get("/api/v1/programs/unreported")
async def get_unreported_programs(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    programs = db.query(models.MiniProgram).filter(
        or_(models.MiniProgram.is_archived == 0, models.MiniProgram.is_archived.is_(None)),
    ).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()
    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    has_stock_map = get_program_has_stock_map(db, program_ids)
    stock_summary_map = get_program_stock_summary_map(db, program_ids)
    stock_change_map = get_program_stock_change_map(db, program_ids)
    today_str = datetime.now().strftime("%Y-%m-%d")

    items = []
    for program in programs:
        last_time_iso = last_updates.get(program.program_id)
        if not last_time_iso or last_time_iso.split("T")[0] != today_str:
            payload = build_program_payload(program, last_updates, has_stock_map, stock_summary_map, stock_change_map)
            payload["last_report_time"] = last_time_iso
            items.append(payload)
    return {"items": items}


@router.get("/api/v1/programs/{program_id}")
async def get_program_detail(program_id: str, sort: Optional[str] = None, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    accounts = db.query(models.WechatAccount).order_by(
        models.WechatAccount.sort_order.asc(),
        models.WechatAccount.id.asc(),
    ).all()
    latest_points_map = get_latest_points_records_for_program(db, program_id)
    reverse_sort = sort != "asc"

    ranking = []
    for account in accounts:
        item = latest_points_map.get(account.wechat_id)
        ranking.append({
            "wechat_id": account.wechat_id,
            "nickname": account.nickname,
            "device": account.device,
            "phone": account.phone,
            "points": item.points if item else 0,
            "report_time": item.report_time.isoformat() if item and item.report_time else None,
        })
    ranking.sort(key=lambda x: x["points"], reverse=reverse_sort)

    last_updates = get_program_last_updates(db, [program_id])
    has_stock_map = get_program_has_stock_map(db, [program_id])
    stock_summary_map = get_program_stock_summary_map(db, [program_id])
    stock_change_map = get_program_stock_change_map(db, [program_id])
    return {
        **build_program_payload(program, last_updates, has_stock_map, stock_summary_map, stock_change_map),
        "ranking": ranking,
    }


@router.get("/api/v1/programs/{program_id}/stock")
async def get_program_stock(program_id: str, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    products = db.query(models.Product).filter(models.Product.program_id == program_id).all()

    tz_offset = timedelta(hours=8)
    now_cst = datetime.utcnow() + tz_offset
    today_cst = now_cst.date()

    subquery = db.query(
        models.PointsHistory.wechat_id,
        func.max(models.PointsHistory.report_time).label("max_time"),
    ).filter(
        models.PointsHistory.program_id == program_id
    ).group_by(models.PointsHistory.wechat_id).subquery()

    max_points_val = db.query(func.max(models.PointsHistory.points)).join(
        subquery,
        and_(
            models.PointsHistory.wechat_id == subquery.c.wechat_id,
            models.PointsHistory.report_time == subquery.c.max_time,
        ),
    ).scalar()

    report_rows = db.query(
        models.StockHistory.product_id,
        func.max(models.StockHistory.change_time).label("last_change_time"),
    ).filter(
        models.StockHistory.program_id == program_id,
    ).group_by(models.StockHistory.product_id).all()

    latest_report_date = None
    previous_report_date = None
    for row in report_rows:
        if not row.last_change_time:
            continue
        report_date = (row.last_change_time + tz_offset).date()
        if latest_report_date is None or report_date > latest_report_date:
            previous_report_date = latest_report_date
            latest_report_date = report_date
        elif report_date != latest_report_date and (previous_report_date is None or report_date > previous_report_date):
            previous_report_date = report_date

    latest_product_ids = set()
    previous_product_ids = set()
    for row in report_rows:
        if not row.last_change_time:
            continue
        report_date = (row.last_change_time + tz_offset).date()
        if report_date == latest_report_date:
            latest_product_ids.add(row.product_id)
        if report_date == previous_report_date:
            previous_product_ids.add(row.product_id)

    added_product_ids = latest_product_ids - previous_product_ids if previous_product_ids else set()
    removed_product_ids = previous_product_ids - latest_product_ids if previous_product_ids else set()
    should_show_changes = latest_report_date == today_cst and previous_report_date is not None

    items = []
    changed_lookup = {}

    for product in products:
        is_visible = product.is_hidden in (0, None)
        change_type = None
        if should_show_changes and product.product_id in added_product_ids:
            change_type = "added"
        elif should_show_changes and product.product_id in removed_product_ids:
            change_type = "removed"

        product_payload = {
            "id": product.id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "points": product.points,
            "stock": product.stock,
            "image_url": normalize_image_url(product),
            "is_hidden": product.is_hidden == 1,
            "hidden_at": product.hidden_at.isoformat() if product.hidden_at else None,
            "change_type": change_type,
        }

        if is_visible:
            items.append(product_payload)

        if change_type:
            changed_lookup[product.product_id] = product_payload

    if should_show_changes and removed_product_ids:
        missing_removed_ids = removed_product_ids - set(changed_lookup.keys())
        if missing_removed_ids:
            removed_products = db.query(models.Product).filter(
                models.Product.program_id == program_id,
                models.Product.product_id.in_(missing_removed_ids),
            ).all()
            for product in removed_products:
                changed_lookup[product.product_id] = {
                    "id": product.id,
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "points": product.points,
                    "stock": product.stock,
                    "image_url": normalize_image_url(product),
                    "is_hidden": product.is_hidden == 1,
                    "hidden_at": product.hidden_at.isoformat() if product.hidden_at else None,
                    "change_type": "removed",
                }

    items.sort(key=lambda x: (x["stock"] <= 0, x["points"]))
    change_items = list(changed_lookup.values())
    change_items.sort(key=lambda x: (0 if x["change_type"] == "added" else 1, x["points"], x["product_name"] or ""))

    added_count = len(added_product_ids) if should_show_changes else 0
    removed_count = len(removed_product_ids) if should_show_changes else 0

    return {
        "program_id": program_id,
        "program_name": program.program_name if program else program_id,
        "max_user_points": max_points_val if max_points_val is not None else 0,
        "product_count": len(items),
        "stock_change": {
            "added_count": added_count,
            "removed_count": removed_count,
            "changed": added_count > 0 or removed_count > 0,
        },
        "products": items,
        "changed_products": change_items,
    }


@router.get("/api/v1/programs/{program_id}/ranking")
async def get_program_ranking(program_id: str, sort: Optional[str] = None, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    accounts = db.query(models.WechatAccount).order_by(
        models.WechatAccount.sort_order.asc(),
        models.WechatAccount.id.asc(),
    ).all()
    latest_points_map = get_latest_points_records_for_program(db, program_id)

    ranking = []
    for account in accounts:
        item = latest_points_map.get(account.wechat_id)
        ranking.append({
            "wechat_id": account.wechat_id,
            "nickname": account.nickname,
            "device": account.device,
            "phone": account.phone,
            "points": item.points if item else 0,
            "report_time": item.report_time.strftime("%Y-%m-%d %H:%M:%S") if item and item.report_time else None,
        })
    ranking.sort(key=lambda x: x["points"], reverse=(sort != "asc"))

    return {
        "program_name": program.program_name if program and program.program_name else program_id,
        "program_id": program_id,
        "ranking": ranking,
    }


@router.get("/api/v1/programs/{program_id}/rankings")
async def get_program_rankings(program_id: str, db: Session = Depends(get_db)):
    ranking_data = await get_program_ranking(program_id=program_id, sort=None, db=db)
    return {
        "program_name": ranking_data["program_name"],
        "rankings": ranking_data["ranking"],
    }


@router.put("/api/v1/programs/{program_id}")
async def update_program(program_id: str, update: ProgramUpdate, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    if not program:
        program = models.MiniProgram(program_id=program_id, program_name=program_id)
        db.add(program)

    if update.auth_type is not None:
        if update.auth_type not in ["code", "token", "app"]:
            raise HTTPException(status_code=400, detail="Invalid auth type")
        program.auth_type = update.auth_type

    if update.is_pinned is not None:
        program.sort_order = 1 if update.is_pinned else 0

    if update.is_favorite is not None:
        program.is_favorite = 1 if update.is_favorite else 0

    if update.note is not None:
        program.note = update.note

    if update.tags is not None:
        program.tags = serialize_program_tags(update.tags)

    if update.is_archived is not None:
        if update.is_archived:
            program.is_archived = 1
            program.archived_at = datetime.utcnow()
            program.is_favorite = 0  # archive auto-clears favorite
        else:
            program.is_archived = 0
            program.archived_at = None

    db.commit()
    return JSONResponse(content={
        "status": "success",
        "tags": get_program_tags(program),
        "is_archived": program.is_archived == 1,
        "archived_at": program.archived_at.isoformat() if program.archived_at else None,
        "is_favorite": program.is_favorite == 1,
    })


@router.delete("/api/v1/programs/{program_id}")
async def delete_program(program_id: str, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    db.query(models.PointsHistory).filter(models.PointsHistory.program_id == program_id).delete()
    db.query(models.Product).filter(models.Product.program_id == program_id).delete()
    if program:
        db.delete(program)
    db.commit()
    return JSONResponse(content={"status": "success"})
