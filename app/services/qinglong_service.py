from sqlalchemy.orm import Session
from app import models, schemas
from app.services import cleanup_service
from datetime import datetime
import uuid
import re

def is_valid_phone(phone: str) -> bool:
    """Check if the string is a valid Chinese mobile phone number."""
    return bool(re.match(r'^1[3-9]\d{9}$', phone))

def process_points_report(db: Session, report: schemas.PointsReportRequest):
    batch_id = str(uuid.uuid4())
    
    for account_data in report.data.wechat_accounts:
        # Determine nickname based on new logic
        target_nickname = account_data.nickname
        is_phone = is_valid_phone(account_data.wechat_id)

        if is_phone:
            # Check if phone number is bound to a WeChat account
            bound_account = db.query(models.WechatAccount).filter(models.WechatAccount.phone == account_data.wechat_id).first()
            if bound_account:
                # If bound, use the WeChat nickname
                target_nickname = bound_account.nickname
            else:
                # If not bound, set user identifier to empty string
                target_nickname = ""

        # 1. Get or create WechatAccount
        account = db.query(models.WechatAccount).filter(models.WechatAccount.wechat_id == account_data.wechat_id).first()
        if not account:
            account = models.WechatAccount(
                wechat_id=account_data.wechat_id,
                nickname=target_nickname
            )
            db.add(account)
            db.flush() # Get ID
        else:
            if is_phone:
                # For phone numbers, always apply the resolved nickname (bound nickname or empty)
                if account.nickname != target_nickname:
                    account.nickname = target_nickname
                    db.add(account)
            else:
                # Original logic for WeChat users
                if account_data.nickname and account.nickname != account_data.nickname:
                    account.nickname = account_data.nickname
                    db.add(account)

        for point_data in account_data.points_data:
            # 2. Get or create MiniProgram
            program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == point_data.program_id).first()
            if not program:
                program = models.MiniProgram(
                    program_id=point_data.program_id,
                    program_name=point_data.program_name
                )
                db.add(program)
                db.flush()
            else:
                if point_data.program_name and program.program_name != point_data.program_name:
                    program.program_name = point_data.program_name
                    db.add(program)
            
            # 3. Record Points History
            # Optional: Check for duplicates within recent time? 
            # For now, just insert as per doc
            history = models.PointsHistory(
                wechat_id=account.wechat_id,
                program_id=program.program_id,
                points=point_data.current_points,
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
    # 1. Get or create Program
    program = db.query(models.MiniProgram).filter(models.MiniProgram.program_id == report.program_id).first()
    if not program:
        # If program doesn't exist, we might create it with default name or fail. 
        # Creating it seems safer.
        program = models.MiniProgram(program_id=report.program_id, program_name="Unknown Program")
        db.add(program)
        db.flush()
    
    updated_products = []
    
    for prod_data in report.products:
        # Determine product_id
        p_id = prod_data.product_id
        if not p_id:
            # Use product_name as ID if not provided. 
            p_id = prod_data.product_name

        # 2. Get or create Product
        product = db.query(models.Product).filter(
            models.Product.program_id == report.program_id,
            models.Product.product_id == p_id
        ).first()
        
        old_stock = 0
        is_new = False
        
        if not product:
            is_new = True
            product = models.Product(
                program_id=report.program_id,
                product_id=p_id,
                product_name=prod_data.product_name,
                image_local_path=None,
                image_url=prod_data.image_url,
                points=prod_data.points or 0,
                stock=prod_data.stock or 0
            )
            db.add(product)
            db.flush() 
        else:
            old_stock = product.stock
            # Update info
            product.product_name = prod_data.product_name
            if prod_data.image_url:
                product.image_url = prod_data.image_url
            if prod_data.points is not None:
                product.points = prod_data.points
            
            if prod_data.stock is not None and prod_data.stock != product.stock:
                product.stock = prod_data.stock
            
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
                change_time=prod_data.last_updated or datetime.utcnow()
            )
            db.add(history)
            updated_products.append(p_id)
            
    # Prune history
    try:
        settings = cleanup_service.get_or_create_settings(db)
        cleanup_service.prune_stock_history(db, settings.max_log_entries, settings.max_retention_days)
    except Exception as e:
        print(f"Error pruning stock history: {e}")

    db.commit()
    return {"status": "success", "updated_products": updated_products}
