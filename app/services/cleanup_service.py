from sqlalchemy.orm import Session
from sqlalchemy import text
from app import models
from datetime import datetime, timedelta


def ensure_system_settings_columns(db: Session):
    expected_columns = {
        "access_protection_enabled": "ALTER TABLE system_settings ADD COLUMN access_protection_enabled INTEGER DEFAULT 0",
        "access_key": "ALTER TABLE system_settings ADD COLUMN access_key VARCHAR(255)",
    }

    connection = db.bind.connect()
    try:
        inspector = db.bind.dialect.get_columns(connection, "system_settings")
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


def get_or_create_settings(db: Session) -> models.SystemSettings:
    ensure_system_settings_columns(db)
    settings = db.query(models.SystemSettings).first()
    if not settings:
        settings = models.SystemSettings(
            max_log_entries=10000,
            max_retention_days=30,
            access_protection_enabled=0,
            access_key=None,
            updated_at=datetime.utcnow()
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def prune_points_history(db: Session, max_entries: int, max_days: int):
    if max_days is not None and max_days > 0:
        threshold = datetime.utcnow() - timedelta(days=max_days)
        db.query(models.PointsHistory).filter(models.PointsHistory.report_time < threshold).delete()
    if max_entries is not None and max_entries > 0:
        # Check current count first to avoid expensive query if not needed
        # But count() is also a query. 
        # The subquery approach is: get IDs beyond limit.
        # If total < max_entries, offset returns empty.
        ids_to_delete = [
            r.id for r in db.query(models.PointsHistory.id)
            .order_by(models.PointsHistory.report_time.desc())
            .offset(max_entries).all()
        ]
        if ids_to_delete:
            db.query(models.PointsHistory).filter(models.PointsHistory.id.in_(ids_to_delete)).delete(synchronize_session=False)

def prune_stock_history(db: Session, max_entries: int, max_days: int):
    if max_days is not None and max_days > 0:
        threshold = datetime.utcnow() - timedelta(days=max_days)
        db.query(models.StockHistory).filter(models.StockHistory.change_time < threshold).delete()
    if max_entries is not None and max_entries > 0:
        ids_to_delete = [
            r.id for r in db.query(models.StockHistory.id)
            .order_by(models.StockHistory.change_time.desc())
            .offset(max_entries).all()
        ]
        if ids_to_delete:
            db.query(models.StockHistory).filter(models.StockHistory.id.in_(ids_to_delete)).delete(synchronize_session=False)
