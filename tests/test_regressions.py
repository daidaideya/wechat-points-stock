from datetime import datetime
from io import BytesIO
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.access_control import AccessAttemptLimiter
from app import models
from app.config import settings
from app.database import Base
from app.dependencies import (
    ACCESS_SESSION_TTL_SECONDS,
    create_ui_access_session,
    is_valid_ui_access_session,
    require_ui_access,
    verify_token,
)
from app.main import health_live, health_ready, resolve_frontend_asset
from app.maintenance import (
    DatabaseMaintenanceBusy,
    database_maintenance,
    is_database_maintenance,
)
from app.routers import stock, web
from app.routers import images
from app.security import hash_access_key, verify_access_key_hash
from app.services import cleanup_service


def make_request(path: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
        }
    )


def test_ingest_token_rejects_missing_or_short_values(monkeypatch):
    monkeypatch.setattr(settings, "INGEST_TOKEN", "default_token")
    with pytest.raises(RuntimeError):
        settings.validate_runtime()

    monkeypatch.setattr(settings, "INGEST_TOKEN", "x" * 31)
    with pytest.raises(RuntimeError):
        settings.validate_runtime()

    monkeypatch.setattr(settings, "INGEST_TOKEN", "x" * 32)
    settings.validate_runtime()


def test_verify_token_uses_ingest_token(monkeypatch):
    monkeypatch.setattr(settings, "INGEST_TOKEN", "expected-token")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expected-token")
    assert verify_token(credentials) == "expected-token"

    wrong_credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-token")
    with pytest.raises(HTTPException) as error:
        verify_token(wrong_credentials)
    assert error.value.status_code == 401


def test_ui_access_dependency_respects_protection(monkeypatch):
    access_settings = SimpleNamespace(access_protection_enabled=1, access_key="ui-secret")
    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: access_settings)
    request = make_request("/api/v1/accounts")

    with pytest.raises(HTTPException) as missing_error:
        require_ui_access(request, None, object())
    assert missing_error.value.status_code == 401

    assert require_ui_access(request, "ui-secret", object()) is None

    public_request = make_request("/api/v1/access/status")
    assert require_ui_access(public_request, None, object()) is None


def test_ui_access_session_is_signed_short_lived_and_bound_to_key():
    session = create_ui_access_session("ui-secret", now=1000)

    assert is_valid_ui_access_session(session, "ui-secret", now=1000)
    assert is_valid_ui_access_session(
        session,
        "ui-secret",
        now=1000 + ACCESS_SESSION_TTL_SECONDS - 1,
    )
    assert not is_valid_ui_access_session(session, "other-secret", now=1000)
    assert not is_valid_ui_access_session(
        session,
        "ui-secret",
        now=1000 + ACCESS_SESSION_TTL_SECONDS,
    )


def test_access_key_migration_hashes_and_clears_legacy_plaintext():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(models.SystemSettings(
        access_protection_enabled=1,
        access_key="legacy-secret",
    ))
    db.commit()

    cleanup_service.ensure_system_settings_columns(db)
    migrated = db.query(models.SystemSettings).first()

    assert migrated.access_key is None
    assert migrated.access_key_hash.startswith("pbkdf2_sha256$")
    assert verify_access_key_hash("legacy-secret", migrated.access_key_hash)
    assert not verify_access_key_hash("wrong-secret", migrated.access_key_hash)
    assert db.query(models.AccessAuditEvent).count() == 0

    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_hashed_ui_access_key_is_accepted_and_signed_session_uses_hash(monkeypatch):
    stored_hash = hash_access_key("ui-secret")
    access_settings = SimpleNamespace(
        access_protection_enabled=1,
        access_key=None,
        access_key_hash=stored_hash,
    )
    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: access_settings)
    request = make_request("/api/v1/accounts")

    assert require_ui_access(request, "ui-secret", object()) is None
    session = create_ui_access_session(stored_hash, now=1000)
    assert is_valid_ui_access_session(session, stored_hash, now=1000)


def test_ui_access_failure_limiter_blocks_and_can_be_cleared():
    limiter = AccessAttemptLimiter(window_seconds=60, max_failures=3, lockout_seconds=120)

    assert limiter.retry_after("test-client", now=1000) == 0
    limiter.record_failure("test-client", now=1000)
    limiter.record_failure("test-client", now=1001)
    limiter.record_failure("test-client", now=1002)
    assert limiter.retry_after("test-client", now=1003) == 119

    limiter.clear("test-client")
    assert limiter.retry_after("test-client", now=1003) == 0


def test_ui_access_dependency_accepts_signed_session(monkeypatch):
    access_settings = SimpleNamespace(access_protection_enabled=1, access_key="ui-secret")
    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: access_settings)
    request = make_request("/api/v1/accounts")
    session = create_ui_access_session("ui-secret")

    assert require_ui_access(request, None, object(), session) is None


def test_access_status_migrates_legacy_header_to_cookie(monkeypatch):
    access_settings = SimpleNamespace(access_protection_enabled=1, access_key="ui-secret")
    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: access_settings)

    response = web.get_access_status(make_request("/api/v1/access/status"), "ui-secret", None, object())

    assert response.status_code == 200
    assert b'"authenticated":true' in response.body
    assert "site_access_session=" in response.headers["set-cookie"]


def test_log_settings_does_not_clear_existing_access_key_on_empty_field(monkeypatch):
    access_settings = SimpleNamespace(
        max_log_entries=100,
        max_retention_days=30,
        access_protection_enabled=1,
        access_key="ui-secret",
        updated_at=None,
    )

    class FakeDB:
        def add(self, _value):
            return None

        def commit(self):
            return None

    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: access_settings)
    monkeypatch.setattr(cleanup_service, "prune_points_history", lambda *args: None)
    monkeypatch.setattr(cleanup_service, "prune_stock_history", lambda *args: None)

    web.update_log_settings(
        web.LogSettingsUpdate(
            max_log_entries=200,
            max_retention_days=60,
            access_protection_enabled=True,
            access_key="",
        ),
        FakeDB(),
    )

    assert access_settings.access_key == "ui-secret"


def test_log_settings_stores_new_access_key_as_hash(monkeypatch):
    access_settings = SimpleNamespace(
        max_log_entries=100,
        max_retention_days=30,
        access_protection_enabled=1,
        access_key="old-secret",
        access_key_hash=None,
        updated_at=None,
    )

    class FakeDB:
        def add(self, _value):
            return None

        def commit(self):
            return None

    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: access_settings)
    monkeypatch.setattr(cleanup_service, "prune_points_history", lambda *args: None)
    monkeypatch.setattr(cleanup_service, "prune_stock_history", lambda *args: None)

    web.update_log_settings(
        web.LogSettingsUpdate(
            max_log_entries=200,
            max_retention_days=60,
            access_protection_enabled=True,
            access_key="new-secret",
        ),
        FakeDB(),
    )

    assert access_settings.access_key is None
    assert verify_access_key_hash("new-secret", access_settings.access_key_hash)


def test_access_audit_persists_without_credential_material():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    request = make_request("/api/v1/access/verify")
    request.state.request_id = "request-123"

    cleanup_service.record_access_audit(db, request, "access_verified")
    event = db.query(models.AccessAuditEvent).one()

    assert event.event_type == "access_verified"
    assert event.client_id == "testclient"
    assert event.request_id == "request-123"
    assert not hasattr(event, "access_key")

    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_database_maintenance_uses_a_cross_process_lock(tmp_path):
    lock_path = str(tmp_path / "database.maintenance.lock")

    assert not is_database_maintenance(lock_path)
    with database_maintenance(lock_path):
        assert is_database_maintenance(lock_path)
        with pytest.raises(DatabaseMaintenanceBusy):
            with database_maintenance(lock_path):
                pass
    assert not is_database_maintenance(lock_path)


def test_database_maintenance_lock_is_visible_to_another_process(tmp_path):
    lock_path = str(tmp_path / "database.maintenance.lock")
    child_code = (
        "import sys\n"
        "from app.maintenance import database_maintenance\n"
        "with database_maintenance(sys.argv[1]):\n"
        "    print('ready', flush=True)\n"
        "    sys.stdin.readline()\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", child_code, lock_path],
        cwd=str(Path(__file__).resolve().parents[1]),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout.readline().strip() == "ready"
        assert is_database_maintenance(lock_path)
        process.stdin.write("\n")
        process.stdin.flush()
        assert process.wait(timeout=5) == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
def test_frontend_asset_resolution_blocks_traversal():
    assert resolve_frontend_asset("assets/app.js") is not None
    assert resolve_frontend_asset("../.env") is None
    assert resolve_frontend_asset("../../data/database.db") is None


def test_health_endpoints_report_runtime_state(monkeypatch):
    class FakeSession:
        def execute(self, _query):
            return None

        def close(self):
            return None

    monkeypatch.setattr("app.main.SessionLocal", lambda: FakeSession())
    assert health_live() == {"status": "ok"}
    assert health_ready()["status"] == "ok"


@pytest.fixture()
def stock_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    program = models.MiniProgram(
        program_id="program-1",
        program_name="示例小程序",
        tags='["游戏", "热门"]',
    )
    other_program = models.MiniProgram(
        program_id="program-2",
        program_name="另一个小程序",
    )
    account = models.WechatAccount(wechat_id="wechat-1", nickname="测试账号")
    db.add_all([program, other_program, account])
    db.flush()
    db.add(models.PointsHistory(
        program_id=program.program_id,
        wechat_id=account.wechat_id,
        points=100,
        cash=5,
        report_time=datetime(2025, 1, 1),
    ))
    db.add(models.PointsHistory(
        program_id=other_program.program_id,
        wechat_id=account.wechat_id,
        points=1000,
        cash=100,
        report_time=datetime(2025, 1, 1),
    ))
    db.add_all([
        models.Product(
            program_id=program.program_id,
            product_id="free-product",
            product_name="纯积分商品",
            points=50,
            cash=0,
            stock=10,
        ),
        models.Product(
            program_id=program.program_id,
            product_id="cash-product",
            product_name="积分加钱商品",
            points=50,
            cash=10,
            stock=10,
        ),
        models.Product(
            program_id=program.program_id,
            product_id="empty-product",
            product_name="无库存商品",
            points=50,
            cash=0,
            stock=0,
        ),
    ])
    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_stock_center_is_server_paginated_and_filterable(stock_db):
    first_page = stock.get_stock_center(
        page=1,
        size=2,
        q=None,
        tag=None,
        status="all",
        price_mode="all",
        cash_max=None,
        db=stock_db,
    )
    assert first_page["total"] == 3
    assert len(first_page["items"]) == 2
    assert first_page["items"][0]["product_id"] == "free-product"
    assert first_page["summary"] == {
        "totalProducts": 3,
        "inStockProducts": 2,
        "outOfStockProducts": 1,
        "redeemableProducts": 1,
        "pointsOnlyProducts": 2,
        "mixedProducts": 1,
    }

    second_page = stock.get_stock_center(
        page=2,
        size=2,
        q=None,
        tag=None,
        status="all",
        price_mode="all",
        cash_max=None,
        db=stock_db,
    )
    assert second_page["total"] == 3
    assert len(second_page["items"]) == 1

    redeemable = stock.get_stock_center(
        page=1,
        size=20,
        q=None,
        tag=None,
        status="redeemable",
        price_mode="all",
        cash_max=None,
        db=stock_db,
    )
    assert redeemable["total"] == 1
    assert redeemable["items"][0]["product_id"] == "free-product"

    mixed = stock.get_stock_center(
        page=1,
        q=None,
        tag=None,
        status="all",
        price_mode="points_plus_cash",
        cash_max=10,
        size=20,
        db=stock_db,
    )
    assert mixed["total"] == 1
    assert mixed["items"][0]["product_id"] == "cash-product"


def test_program_stock_does_not_mix_same_time_other_program_balance(stock_db):
    payload = web.get_program_stock("program-1", stock_db)
    assert payload["max_user_points"] == 100
    assert payload["max_user_cash"] == 5


def test_off_shelf_endpoint_is_server_paginated(stock_db):
    products = stock_db.query(models.Product).order_by(models.Product.id.asc()).all()
    products[0].is_unlisted = 1
    products[1].is_unlisted = 1
    stock_db.commit()

    page = stock.get_off_shelf_products(
        page=1,
        size=1,
        q=None,
        db=stock_db,
    )
    assert page["total"] == 2
    assert len(page["items"]) == 1
    assert page["items"][0]["total_count"] == 2


def test_image_upload_rejects_wrong_type_and_oversize(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    unsupported = images.UploadFile(
        file=BytesIO(b"not-an-image"),
        filename="payload.txt",
        headers={"content-type": "text/plain"},
    )
    with pytest.raises(HTTPException) as type_error:
        images.upload_image(unsupported, None, None, None)
    assert type_error.value.status_code == 415

    monkeypatch.setattr(images, "MAX_UPLOAD_BYTES", 32)
    oversized = images.UploadFile(
        file=BytesIO(b"\x89PNG\r\n\x1a\n" + b"x" * 40),
        filename="payload.png",
        headers={"content-type": "image/png"},
    )
    with pytest.raises(HTTPException) as size_error:
        images.upload_image(oversized, None, None, None)
    assert size_error.value.status_code == 413
    assert list(tmp_path.iterdir()) == []
