from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app import models
from app.database import Base
from app.services import cleanup_service


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def make_request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/access/verify",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
        }
    )


def test_prune_access_audit_events_removes_expired_rows(db):
    now = datetime.utcnow()
    db.add_all(
        [
            models.AccessAuditEvent(
                event_type="expired",
                event_time=now - timedelta(days=91),
            ),
            models.AccessAuditEvent(
                event_type="recent",
                event_time=now - timedelta(days=89),
            ),
        ]
    )
    db.commit()

    cleanup_service.prune_access_audit_events(db, max_days=90, max_entries=10000)
    db.commit()

    assert [event.event_type for event in db.query(models.AccessAuditEvent).all()] == [
        "recent"
    ]


def test_prune_access_audit_events_keeps_only_newest_entries(db):
    now = datetime.utcnow()
    db.add_all(
        [
            models.AccessAuditEvent(
                event_type=f"event-{index}",
                event_time=now - timedelta(minutes=index),
            )
            for index in range(5)
        ]
    )
    db.commit()

    cleanup_service.prune_access_audit_events(db, max_days=0, max_entries=2)
    db.commit()

    retained = (
        db.query(models.AccessAuditEvent)
        .order_by(models.AccessAuditEvent.event_time.desc(), models.AccessAuditEvent.id.desc())
        .all()
    )
    assert [event.event_type for event in retained] == ["event-0", "event-1"]


def test_prune_access_audit_events_uses_id_as_timestamp_tiebreaker(db):
    event_time = datetime.utcnow()
    db.add_all(
        [
            models.AccessAuditEvent(event_type="first", event_time=event_time),
            models.AccessAuditEvent(event_type="second", event_time=event_time),
            models.AccessAuditEvent(event_type="third", event_time=event_time),
        ]
    )
    db.commit()

    cleanup_service.prune_access_audit_events(db, max_days=0, max_entries=2)
    db.commit()

    retained = (
        db.query(models.AccessAuditEvent)
        .order_by(models.AccessAuditEvent.id.asc())
        .all()
    )
    assert [event.event_type for event in retained] == ["second", "third"]


def test_audit_retention_failure_does_not_fail_audit_write(db, monkeypatch):
    def fail_prune(*_args, **_kwargs):
        raise RuntimeError("temporary cleanup failure")

    monkeypatch.setattr(cleanup_service, "prune_access_audit_events", fail_prune)
    monkeypatch.setattr(cleanup_service, "_last_access_audit_prune_at", 0.0)

    cleanup_service.record_access_audit(db, make_request(), "access_verified")

    events = db.query(models.AccessAuditEvent).all()
    assert len(events) == 1
    assert events[0].event_type == "access_verified"


def test_audit_retention_is_throttled_between_writes(db, monkeypatch):
    prune_calls = []

    def record_prune_call(*_args, **_kwargs):
        prune_calls.append(True)

    monkeypatch.setattr(
        cleanup_service,
        "prune_access_audit_events",
        record_prune_call,
    )
    monkeypatch.setattr(cleanup_service, "_last_access_audit_prune_at", 0.0)

    cleanup_service.record_access_audit(db, make_request(), "access_verified")
    cleanup_service.record_access_audit(db, make_request(), "access_verified")

    assert len(prune_calls) == 1
