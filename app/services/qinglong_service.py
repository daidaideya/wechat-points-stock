from sqlalchemy import func
from sqlalchemy.orm import Session
from app import models, schemas
from app.services import cleanup_service
from app.routers.stock import ensure_product_columns
from datetime import datetime, timedelta
from typing import Optional
import uuid
import re

def is_valid_phone(phone: str) -> bool:
    """Check if the string is a valid Chinese mobile phone number."""
    return bool(re.match(r"^1[3-9]\d{9}$", str(phone or "").strip()))


def _normalize_phone(value: Optional[str]) -> Optional[str]:
    text = "".join(ch for ch in str(value or "") if ch.isdigit())
    if is_valid_phone(text):
        return text
    return None


def next_account_sort_order(db: Session) -> int:
    """Append new accounts to the end of the user list (sort_order ASC)."""
    current_max = db.query(func.max(models.WechatAccount.sort_order)).scalar()
    if current_max is None:
        return 0
    try:
        return int(current_max) + 1
    except (TypeError, ValueError):
        return 0


def resolve_report_account(db: Session, account_data: schemas.WechatAccountData) -> models.WechatAccount:
    """Resolve WechatAccount for a report row.

    APP scripts usually only know a phone number. Rules:
    1. Prefer explicit `phone` field, else detect phone-shaped `wechat_id`.
    2. Prefer an existing account already bound by `phone`.
    3. Else match by `wechat_id`.
    4. Create new account if needed.
    5. Always keep phone numbers in the `phone` column — never leave them only in wechat_id.
    """
    explicit_phone = _normalize_phone(getattr(account_data, "phone", None))
    id_as_phone = _normalize_phone(account_data.wechat_id)
    phone = explicit_phone or id_as_phone
    is_phone_identity = bool(id_as_phone) and not explicit_phone

    account = None
    if phone:
        account = (
            db.query(models.WechatAccount)
            .filter(models.WechatAccount.phone == phone)
            .order_by(models.WechatAccount.id.asc())
            .first()
        )
    if not account:
        account = (
            db.query(models.WechatAccount)
            .filter(models.WechatAccount.wechat_id == account_data.wechat_id)
            .first()
        )
    # Legacy rows: wechat_id was filled with the phone number.
    if not account and phone:
        account = (
            db.query(models.WechatAccount)
            .filter(models.WechatAccount.wechat_id == phone)
            .first()
        )

    if account:
        changed = False
        if phone and (account.phone or "").strip() != phone:
            account.phone = phone
            changed = True

        if phone and is_phone_identity:
            # Phone-only report: do not invent a nickname; keep bound WeChat nickname if any.
            if account.wechat_id == phone and not (account.nickname or "").strip():
                # leave nickname empty — UI shows phone primarily
                pass
            # Prefer not overwriting a real WeChat nickname with empty.
        elif account_data.nickname and account.nickname != account_data.nickname:
            account.nickname = account_data.nickname
            changed = True

        if changed:
            db.add(account)
            db.flush()
        return account

    # Create — always append to list end (do not steal front with default sort_order=0).
    sort_order = next_account_sort_order(db)
    if phone:
        # Stable internal id for phone-primary APP users: keep wechat_id == phone for
        # points_history FK continuity with older scripts, but ALWAYS store phone column.
        account = models.WechatAccount(
            wechat_id=phone if is_phone_identity else account_data.wechat_id,
            nickname=(account_data.nickname if account_data.nickname is not None else "") or "",
            phone=phone,
            sort_order=sort_order,
        )
    else:
        account = models.WechatAccount(
            wechat_id=account_data.wechat_id,
            nickname=account_data.nickname,
            phone=None,
            sort_order=sort_order,
        )
    db.add(account)
    db.flush()
    return account


def process_points_report(db: Session, report: schemas.PointsReportRequest):
    cleanup_service.ensure_points_history_columns(db)
    batch_id = str(uuid.uuid4())

    for account_data in report.data.wechat_accounts:
        # 1. Resolve account (phone-primary for APP scripts)
        account = resolve_report_account(db, account_data)

        for point_data in account_data.points_data:
            # 2. Get or create MiniProgram
            program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == point_data.program_id).first()
            # Normalize optional auth_type from QingLong scripts (code/token/app).
            raw_auth = getattr(point_data, "auth_type", None)
            auth_type = None
            if raw_auth is not None:
                auth_type = str(raw_auth).strip().lower() or None
                if auth_type not in {"code", "token", "app"}:
                    auth_type = None

            if not program:
                program = models.MiniProgram(
                    program_id=point_data.program_id,
                    program_name=point_data.program_name,
                    auth_type=auth_type or "code",
                )
                db.add(program)
                db.flush()
            else:
                changed = False
                if point_data.program_name and program.program_name != point_data.program_name:
                    program.program_name = point_data.program_name
                    changed = True
                # Only set auth_type when the script explicitly sends it (APP list needs app).
                if auth_type and getattr(program, "auth_type", None) != auth_type:
                    program.auth_type = auth_type
                    changed = True
                if changed:
                    db.add(program)
            
            # 3. Record Points History (points and/or cash)
            # Round to 4 decimal places to avoid float noise while supporting 0.1-style balances.
            # Missing dimension stays NULL so "not reported" ≠ "zero".
            points_value = None
            if point_data.current_points is not None:
                points_value = round(float(point_data.current_points), 4)
            cash_value = None
            if point_data.current_cash is not None:
                cash_value = round(float(point_data.current_cash), 4)

            history = models.PointsHistory(
                wechat_id=account.wechat_id,
                program_id=program.program_id,
                points=points_value,
                cash=cash_value,
                report_time=report.execution_time or datetime.utcnow(),
                batch_id=batch_id
            )
            db.add(history)
    
    # Prune history
    try:
        settings = cleanup_service.get_or_create_settings(db)
        cleanup_service.prune_points_history(db, settings.max_log_entries, settings.max_retention_days)
    except Exception as e:
        # Just log error, don't fail the request
        print(f"Error pruning points history: {e}")

    db.commit()
    return {"status": "success", "batch_id": batch_id}

def process_stock_report(db: Session, report: schemas.StockReportRequest):
    ensure_product_columns(db)

    # 1. Get or create Program
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == report.program_id).first()
    if not program:
        # If program doesn't exist, we might create it with default name or fail.
        # Creating it seems safer.
        program = models.MiniProgram(program_id=report.program_id, program_name="Unknown Program")
        db.add(program)
        db.flush()

    report_timestamp = report.products[0].last_updated if report.products and report.products[0].last_updated else datetime.utcnow()
    report_day_start = datetime.combine(report_timestamp.date(), datetime.min.time())
    current_report_product_ids = set()
    updated_products = []

    # 与「最近一次有报告的那天」对比，找出本次没出现的老商品。
    # 如果今天已经报过一次，再次跑这次报告时不应自相对比，所以排除掉今天的 history。
    last_reporting_time = db.query(func.max(models.StockHistory.change_time)).filter(
        models.StockHistory.program_id == report.program_id,
        models.StockHistory.change_time < report_day_start,
    ).scalar()
    last_reporting_product_ids = set()
    if last_reporting_time:
        last_reporting_day_start = datetime.combine(last_reporting_time.date(), datetime.min.time())
        last_reporting_day_end = last_reporting_day_start + timedelta(days=1)
        rows = db.query(models.StockHistory.product_id).filter(
            models.StockHistory.program_id == report.program_id,
            models.StockHistory.change_time >= last_reporting_day_start,
            models.StockHistory.change_time < last_reporting_day_end,
        ).distinct().all()
        last_reporting_product_ids = {row.product_id for row in rows}

    for prod_data in report.products:
        # Determine product_id
        p_id = prod_data.product_id
        if not p_id:
            # Use product_name as ID if not provided.
            p_id = prod_data.product_name

        current_report_product_ids.add(p_id)

        # 2. Get or create Product
        product = db.query(models.Product).filter(
            models.Product.program_id == report.program_id,
            models.Product.product_id == p_id
        ).first()

        old_stock = 0
        is_new = False

        # Normalize mixed redeem cost: points + optional cash (yuan).
        product_points = int(prod_data.points or 0)
        product_cash = float(prod_data.cash or 0)

        if not product:
            is_new = True
            product = models.Product(
                program_id=report.program_id,
                product_id=p_id,
                product_name=prod_data.product_name,
                image_local_path=None,
                image_url=prod_data.image_url,
                points=product_points,
                cash=product_cash,
                stock=prod_data.stock or 0,
                is_hidden=0,
                hidden_at=None,
                is_unlisted=0,
                unlisted_at=None,
            )
            db.add(product)
            db.flush()
        else:
            old_stock = product.stock
            # Update info
            product.product_name = prod_data.product_name
            if prod_data.image_url:
                product.image_url = prod_data.image_url
            # Always refresh price so 积分加钱购 / 纯积分切换能同步过来。
            product.points = product_points
            product.cash = product_cash

            if prod_data.stock is not None and prod_data.stock != product.stock:
                product.stock = prod_data.stock

            # 商品又出现在最新报告里，自动取消下架。is_hidden（手动隐藏）保持不动。
            if product.is_unlisted:
                product.is_unlisted = 0
                product.unlisted_at = None

            db.add(product)

        # 3. Record Stock History if changed or new
        current_stock = product.stock
        # If it's new, we record. If it's existing and stock changed, we record.
        stock_changed = (prod_data.stock is not None and old_stock != current_stock)

        if is_new or stock_changed:
            history = models.StockHistory(
                program_id=report.program_id,
                product_id=p_id,
                old_stock=old_stock,
                new_stock=current_stock,
                change_time=prod_data.last_updated or report_timestamp
            )
            db.add(history)
            updated_products.append(p_id)

    # 上次有报告时存在、本次没出现 → 自动下架。注意只动 is_unlisted，不污染 is_hidden。
    products_to_unlist = last_reporting_product_ids - current_report_product_ids
    if products_to_unlist:
        products = db.query(models.Product).filter(
            models.Product.program_id == report.program_id,
            models.Product.product_id.in_(products_to_unlist)
        ).all()
        for product in products:
            if not product.is_unlisted:
                product.is_unlisted = 1
                product.unlisted_at = report_timestamp
                db.add(product)

    # Prune history
    try:
        settings = cleanup_service.get_or_create_settings(db)
        cleanup_service.prune_stock_history(db, settings.max_log_entries, settings.max_retention_days)
    except Exception as e:
        print(f"Error pruning stock history: {e}")

    db.commit()
    return {"status": "success", "updated_products": updated_products, "unlisted_products": list(products_to_unlist)}
