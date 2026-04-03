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


def get_all_distinct_tags(db: Session) -> List[str]:
    rows = db.query(models.MiniProgram.tags).filter(
        models.MiniProgram.tags.isnot(None),
        models.MiniProgram.tags != "",
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


def build_program_payload(program, last_updates, has_stock_map):
    return {
        "id": program.id,
        "program_id": program.program_id,
        "program_name": program.program_name,
        "auth_type": program.auth_type,
        "sort_order": program.sort_order,
        "is_favorite": program.is_favorite == 1,
        "last_update_time": last_updates.get(program.program_id),
        "has_stock": has_stock_map.get(program.program_id, False),
        "note": program.note,
        "tags": get_program_tags(program),
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


def build_account_points_summary(db: Session, account: models.WechatAccount, all_programs):
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
                "program_name": current.program.program_name if current.program else current.program_id,
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
        if current.points != 0:
            active_program_count += 1
        points_items.append({
            "program_id": current.program_id,
            "program_name": current.program.program_name if current.program else current.program_id,
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
    account_count = db.query(models.WechatAccount).count()
    program_count = db.query(models.MiniProgram).count()
    points_records_count = db.query(models.PointsHistory).count()
    total_products_count = db.query(models.Product).count()
    out_of_stock_count = db.query(models.Product).filter(models.Product.stock == 0).count()
    favorite_count = db.query(models.MiniProgram).filter(models.MiniProgram.is_favorite == 1).count()
    token_auth_count = db.query(models.MiniProgram).filter(models.MiniProgram.auth_type == "token").count()
    cached_images_count = db.query(models.Product).filter(models.Product.image_local_path.isnot(None)).count()

    programs = db.query(models.MiniProgram).all()
    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    today_str = datetime.now().strftime("%Y-%m-%d")
    unreported_count = 0
    for program_id in program_ids:
        last_time_iso = last_updates.get(program_id)
        if not last_time_iso or last_time_iso.split("T")[0] != today_str:
            unreported_count += 1

    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_day_utc = start_of_day - timedelta(hours=8)
    active_accounts_today = db.query(models.PointsHistory.wechat_id).filter(
        models.PointsHistory.report_time >= start_of_day_utc
    ).distinct().count()

    raw_history = db.query(models.PointsHistory).order_by(models.PointsHistory.report_time.desc()).limit(50).all()
    recent_program_updates = []
    seen_programs = set()
    for item in raw_history:
        if item.program_id in seen_programs:
            continue
        recent_program_updates.append({
            "program_id": item.program_id,
            "program_name": item.program.program_name if item.program else item.program_id,
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
        "recent_program_updates": recent_program_updates,
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
    accounts = db.query(models.WechatAccount).order_by(
        models.WechatAccount.sort_order.asc(),
        models.WechatAccount.id.asc(),
    ).all()
    all_programs = db.query(models.MiniProgram).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()

    items = []
    for account in accounts:
        summary = build_account_points_summary(db, account, all_programs)
        items.append({
            **summary["account"],
            "active_program_count": summary["active_program_count"],
        })
    return {"items": items}


@router.get("/api/v1/accounts/{wechat_id}")
async def get_account(wechat_id: str, db: Session = Depends(get_db)):
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    all_programs = db.query(models.MiniProgram).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()
    return build_account_points_summary(db, account, all_programs)


@router.get("/api/v1/accounts/{wechat_id}/points_details")
async def get_account_points_details(wechat_id: str, db: Session = Depends(get_db)):
    account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == wechat_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    all_programs = db.query(models.MiniProgram).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()
    return build_account_points_summary(db, account, all_programs)["points"]


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
    accounts = db.query(models.WechatAccount).order_by(
        models.WechatAccount.sort_order.asc(),
        models.WechatAccount.id.asc(),
    ).all()
    ensure_mini_program_columns(db)
    all_programs = db.query(models.MiniProgram).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()

    items = []
    for account in accounts:
        summary = build_account_points_summary(db, account, all_programs)
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
    db: Session = Depends(get_db),
):
    ensure_mini_program_columns(db)
    query = db.query(models.MiniProgram)
    programs = []
    total = 0

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
    items = [build_program_payload(program, last_updates, has_stock_map) for program in programs]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "has_more": (page * size) < total,
        "available_tags": get_all_distinct_tags(db),
        "current_tag": normalized_tag or None,
    }


@router.get("/api/v1/programs/favorites")
async def get_favorite_programs(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    programs = db.query(models.MiniProgram).filter(
        models.MiniProgram.is_favorite == 1,
    ).order_by(
        models.MiniProgram.sort_order.desc(),
        models.MiniProgram.id.asc(),
    ).all()
    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    has_stock_map = get_program_has_stock_map(db, program_ids)
    return {
        "items": [build_program_payload(program, last_updates, has_stock_map) for program in programs]
    }


@router.get("/api/v1/programs/unreported")
async def get_unreported_programs(db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    programs = db.query(models.MiniProgram).order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc()).all()
    program_ids = [program.program_id for program in programs]
    last_updates = get_program_last_updates(db, program_ids)
    has_stock_map = get_program_has_stock_map(db, program_ids)
    today_str = datetime.now().strftime("%Y-%m-%d")

    items = []
    for program in programs:
        last_time_iso = last_updates.get(program.program_id)
        if not last_time_iso or last_time_iso.split("T")[0] != today_str:
            payload = build_program_payload(program, last_updates, has_stock_map)
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
    return {
        **build_program_payload(program, last_updates, has_stock_map),
        "ranking": ranking,
    }


@router.get("/api/v1/programs/{program_id}/stock")
async def get_program_stock(program_id: str, db: Session = Depends(get_db)):
    ensure_mini_program_columns(db)
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == program_id).first()
    products = db.query(models.Product).filter(models.Product.program_id == program_id).all()

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

    items = []
    for product in products:
        items.append({
            "id": product.id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "points": product.points,
            "stock": product.stock,
            "image_url": normalize_image_url(product),
        })
    items.sort(key=lambda x: (x["stock"] <= 0, x["points"]))

    return {
        "program_id": program_id,
        "program_name": program.program_name if program else program_id,
        "max_user_points": max_points_val if max_points_val is not None else 0,
        "products": items,
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

    db.commit()
    return JSONResponse(content={
        "status": "success",
        "tags": get_program_tags(program),
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
