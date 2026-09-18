from types import SimpleNamespace

from app.routers import web
from app.services import cleanup_service
from starlette.requests import Request


def make_request(path: str) -> Request:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
        }
    )
    request.state.request_id = "request-high-risk-1"
    return request


def test_settings_update_records_high_risk_audit_without_payload(monkeypatch):
    settings = SimpleNamespace(
        max_log_entries=100,
        max_retention_days=30,
        access_protection_enabled=0,
        access_key=None,
        access_key_hash=None,
        updated_at=None,
    )

    class FakeDB:
        def add(self, _value):
            return None

        def commit(self):
            return None

    events = []
    monkeypatch.setattr(cleanup_service, "get_or_create_settings", lambda _db: settings)
    monkeypatch.setattr(cleanup_service, "prune_points_history", lambda *args: None)
    monkeypatch.setattr(cleanup_service, "prune_stock_history", lambda *args: None)
    monkeypatch.setattr(
        cleanup_service,
        "record_access_audit",
        lambda db, request, event_type: events.append((db, request, event_type)),
    )

    request = make_request("/api/v1/settings/logs")
    web.update_log_settings(
        web.LogSettingsUpdate(
            max_log_entries=200,
            max_retention_days=60,
            access_protection_enabled=True,
            access_key="new-secret",
        ),
        FakeDB(),
        request,
    )

    assert [(event[1].state.request_id, event[2]) for event in events] == [
        ("request-high-risk-1", "settings_logs_updated"),
    ]
