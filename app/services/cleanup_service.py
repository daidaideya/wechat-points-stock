from sqlalchemy.orm import Session
from sqlalchemy import text
from app import models
from app.security import hash_access_key
from datetime import datetime, timedelta


def ensure_system_settings_columns(db: Session):
    expected_columns = {
        "access_protection_enabled": "ALTER TABLE system_settings ADD COLUMN access_protection_enabled INTEGER DEFAULT 0",
        "access_key": "ALTER TABLE system_settings ADD COLUMN access_key VARCHAR(255)",
        "access_key_hash": "ALTER TABLE system_settings ADD COLUMN access_key_hash VARCHAR(255)",
        "ql_base_url": "ALTER TABLE system_settings ADD COLUMN ql_base_url VARCHAR(255)",
        "ql_client_id": "ALTER TABLE system_settings ADD COLUMN ql_client_id VARCHAR(100)",
        "ql_client_secret": "ALTER TABLE system_settings ADD COLUMN ql_client_secret VARCHAR(255)",
        "ql_auto_sync_minutes": "ALTER TABLE system_settings ADD COLUMN ql_auto_sync_minutes INTEGER DEFAULT 5",
        "ql_sync_mode": "ALTER TABLE system_settings ADD COLUMN ql_sync_mode VARCHAR(20) DEFAULT 'auto'",
        "ql_last_sync_at": "ALTER TABLE system_settings ADD COLUMN ql_last_sync_at DATETIME",
        "ql_last_sync_status": "ALTER TABLE system_settings ADD COLUMN ql_last_sync_status VARCHAR(255)",
        "bark_enabled": "ALTER TABLE system_settings ADD COLUMN bark_enabled INTEGER DEFAULT 0",
        "bark_server": "ALTER TABLE system_settings ADD COLUMN bark_server VARCHAR(255)",
        "bark_device_key": "ALTER TABLE system_settings ADD COLUMN bark_device_key VARCHAR(255)",
        "bark_push_time": "ALTER TABLE system_settings ADD COLUMN bark_push_time VARCHAR(16)",
        "bark_last_push_at": "ALTER TABLE system_settings ADD COLUMN bark_last_push_at DATETIME",
        "bark_last_push_status": "ALTER TABLE system_settings ADD COLUMN bark_last_push_status VARCHAR(255)",
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

    if missing_statements:
        for statement in missing_statements:
            db.execute(text(statement))
        db.commit()

    _migrate_plaintext_access_keys(db)
    ensure_access_audit_table(db)


def ensure_access_audit_table(db: Session):
    """Create the audit table for databases initialized before this model."""
    models.AccessAuditEvent.__table__.create(bind=db.bind, checkfirst=True)


def _migrate_plaintext_access_keys(db: Session):
    """Convert legacy access keys to hashes and remove the plaintext copy."""
    settings_rows = db.query(models.SystemSettings).all()
    changed = False
    for settings in settings_rows:
        legacy_key = (getattr(settings, "access_key", None) or "").strip()
        stored_hash = (getattr(settings, "access_key_hash", None) or "").strip()

        if legacy_key and not stored_hash:
            settings.access_key_hash = hash_access_key(legacy_key)
            settings.access_key = None
            changed = True
        elif stored_hash and legacy_key:
            # A partially completed deployment may have both fields. The hash
            # is authoritative, so discard the redundant plaintext value.
            settings.access_key = None
            changed = True

    if changed:
        db.commit()


def record_access_audit(db: Session, request, event_type: str):
    """Persist a low-cardinality access event without ever storing a key."""
    client = getattr(request, "client", None)
    client_id = getattr(client, "host", None) or "unknown"
    request_state = getattr(request, "state", None)
    request_id = getattr(request_state, "request_id", None)
    event = models.AccessAuditEvent(
        event_type=str(event_type)[:40],
        client_id=str(client_id)[:128],
        request_id=str(request_id)[:128] if request_id else None,
    )

    try:
        db.add(event)
        db.commit()
    except Exception:
        # Authentication must remain available even if an audit write is
        # temporarily unavailable. The failure is intentionally not logged
        # with request data or credential material.
        rollback = getattr(db, "rollback", None)
        if rollback:
            rollback()


def ensure_points_history_columns(db: Session):
    """Add cash column for dual points/cash reports (lazy migrate)."""
    expected_columns = {
        "cash": "ALTER TABLE points_history ADD COLUMN cash FLOAT",
    }

    connection = db.bind.connect()
    try:
        inspector = db.bind.dialect.get_columns(connection, "points_history")
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
