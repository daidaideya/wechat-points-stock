import asyncio
from datetime import datetime

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.dependencies import (
    ACCESS_SESSION_COOKIE,
    create_ui_access_session,
)
from app.routers import web
from app.security import hash_access_key


def _build_test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    db.add(
        models.SystemSettings(
            access_protection_enabled=1,
            access_key_hash=hash_access_key("ui-secret"),
        )
    )
    db.commit()

    app = FastAPI()
    app.include_router(web.router)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return app, db, engine


def _request(app, method, path, *, cookies=None, json=None):
    async def request():
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://testserver",
            cookies=cookies or {},
        ) as client:
            return await client.request(method, path, json=json)

    return asyncio.run(request())


def _get(app, path, *, cookies=None):
    return _request(app, "GET", path, cookies=cookies)


def _access_cookie(db):
    settings = db.query(models.SystemSettings).one()
    return {ACCESS_SESSION_COOKIE: create_ui_access_session(settings.access_key_hash)}


def _close_test_db(db, engine):
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_audit_endpoint_requires_ui_access():
    app, db, engine = _build_test_app()
    try:
        response = _get(app, "/api/v1/access/audit-events")
        assert response.status_code == 401
        assert response.json()["detail"] == "访问密钥错误或未提供"
    finally:
        _close_test_db(db, engine)


def test_audit_endpoint_paginates_filters_and_sorts_without_sensitive_fields():
    app, db, engine = _build_test_app()
    try:
        db.add_all(
            [
                models.AccessAuditEvent(
                    event_type="access_failed",
                    client_id="10.0.0.1",
                    request_id="request-1",
                    event_time=datetime(2026, 1, 1, 0, 0, 0),
                ),
                models.AccessAuditEvent(
                    event_type="access_verified",
                    client_id="10.0.0.1",
                    request_id="request-2",
                    event_time=datetime(2026, 1, 1, 0, 0, 0),
                ),
                models.AccessAuditEvent(
                    event_type="access_header_accepted",
                    client_id="10.0.0.2",
                    request_id="request-3",
                    event_time=datetime(2026, 1, 2, 0, 0, 0),
                ),
                models.AccessAuditEvent(
                    event_type="access_rate_limited",
                    client_id="10.0.0.1",
                    request_id="request-4",
                    event_time=datetime(2025, 12, 31, 0, 0, 0),
                ),
                models.AccessAuditEvent(
                    event_type="access_failed",
                    client_id="10.0.0.2",
                    request_id="request-5",
                    event_time=datetime(2026, 1, 1, 0, 0, 0),
                ),
            ]
        )
        db.commit()
        cookies = _access_cookie(db)

        first_page = _get(
            app,
            "/api/v1/access/audit-events?page=1&size=2",
            cookies=cookies,
        )
        assert first_page.status_code == 200
        first_body = first_page.json()
        assert first_body["page"] == 1
        assert first_body["size"] == 2
        assert first_body["total"] == 5
        assert first_body["has_more"] is True
        assert [item["request_id"] for item in first_body["items"]] == [
            "request-3",
            "request-5",
        ]
        assert set(first_body["items"][0]) == {
            "event_type",
            "client_id",
            "request_id",
            "event_time",
        }
        assert "id" not in first_body["items"][0]
        assert "access_key" not in first_body["items"][0]

        second_page = _get(
            app,
            "/api/v1/access/audit-events?page=2&size=2",
            cookies=cookies,
        )
        assert [item["request_id"] for item in second_page.json()["items"]] == [
            "request-2",
            "request-1",
        ]
        assert second_page.json()["has_more"] is True

        last_page = _get(
            app,
            "/api/v1/access/audit-events?page=3&size=2",
            cookies=cookies,
        )
        assert [item["request_id"] for item in last_page.json()["items"]] == [
            "request-4",
        ]
        assert last_page.json()["has_more"] is False

        filtered = _get(
            app,
            "/api/v1/access/audit-events?event_type=access_failed&size=100",
            cookies=cookies,
        )
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 2
        assert [item["request_id"] for item in filtered.json()["items"]] == [
            "request-5",
            "request-1",
        ]

        by_client = _get(
            app,
            "/api/v1/access/audit-events?client_id=10.0.0.1&size=100",
            cookies=cookies,
        )
        assert by_client.status_code == 200
        assert by_client.json()["total"] == 3
        assert [item["request_id"] for item in by_client.json()["items"]] == [
            "request-2",
            "request-1",
            "request-4",
        ]
    finally:
        _close_test_db(db, engine)


def test_audit_query_size_and_page_are_bounded_by_api_contract():
    app, db, engine = _build_test_app()
    try:
        cookies = _access_cookie(db)
        assert _get(
            app,
            "/api/v1/access/audit-events?page=0&size=20",
            cookies=cookies,
        ).status_code == 422
        assert _get(
            app,
            "/api/v1/access/audit-events?page=1&size=101",
            cookies=cookies,
        ).status_code == 422
    finally:
        _close_test_db(db, engine)


def test_access_status_and_verify_remain_public():
    app, db, engine = _build_test_app()
    try:
        status_response = _get(app, "/api/v1/access/status")
        assert status_response.status_code == 200
        assert status_response.json()["enabled"] is True
        assert status_response.json()["authenticated"] is False

        verify_response = _request(
            app,
            "POST",
            "/api/v1/access/verify",
            json={"access_key": "wrong-secret"},
        )
        assert verify_response.status_code == 401
        assert verify_response.json()["detail"] == "访问密钥错误"
    finally:
        _close_test_db(db, engine)
