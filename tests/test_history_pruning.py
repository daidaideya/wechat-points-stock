from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.services.cleanup_service import (
    prune_points_history,
    prune_stock_history,
)


@pytest.fixture()
def history_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _history_case(kind):
    if kind == "points":
        return (
            models.PointsHistory,
            "report_time",
            prune_points_history,
        )
    return (
        models.StockHistory,
        "change_time",
        prune_stock_history,
    )


def _make_history(kind, row_id, timestamp):
    if kind == "points":
        return models.PointsHistory(
            id=row_id,
            wechat_id="wechat-1",
            program_id="program-1",
            points=float(row_id),
            report_time=timestamp,
        )
    return models.StockHistory(
        id=row_id,
        program_id="program-1",
        product_id=f"product-{row_id}",
        old_stock=row_id,
        new_stock=row_id + 1,
        change_time=timestamp,
    )


def _remaining_ids(db, kind):
    model, timestamp_name, _ = _history_case(kind)
    timestamp_column = getattr(model, timestamp_name)
    return [
        row.id
        for row in db.query(model)
        .order_by(timestamp_column.desc(), model.id.desc())
        .all()
    ]


@pytest.mark.parametrize("kind", ["points", "stock"])
def test_pruning_empty_history_is_a_noop(history_db, kind):
    _, _, prune = _history_case(kind)

    prune(history_db, max_entries=3, max_days=7)

    assert _remaining_ids(history_db, kind) == []


@pytest.mark.parametrize("kind", ["points", "stock"])
def test_pruning_keeps_history_below_max_entries(history_db, kind):
    now = datetime.utcnow()
    history_db.add_all(
        [_make_history(kind, row_id, now - timedelta(hours=row_id)) for row_id in (1, 2)]
    )
    history_db.flush()
    _, _, prune = _history_case(kind)

    prune(history_db, max_entries=3, max_days=0)

    assert _remaining_ids(history_db, kind) == [1, 2]


@pytest.mark.parametrize("kind", ["points", "stock"])
def test_pruning_over_limit_uses_stable_id_tie_breaker(history_db, kind):
    same_timestamp = datetime(2025, 1, 1, 12, 0, 0)
    history_db.add_all(
        [_make_history(kind, row_id, same_timestamp) for row_id in range(1, 6)]
    )
    history_db.flush()
    _, _, prune = _history_case(kind)

    prune(history_db, max_entries=3, max_days=0)

    # At one timestamp, the larger IDs are the deterministic newest rows.
    assert _remaining_ids(history_db, kind) == [5, 4, 3]


@pytest.mark.parametrize("kind", ["points", "stock"])
def test_pruning_applies_max_days_before_max_entries(history_db, kind):
    now = datetime.utcnow()
    history_db.add_all([
        _make_history(kind, 1, now - timedelta(days=10)),
        _make_history(kind, 2, now - timedelta(days=4)),
        _make_history(kind, 3, now - timedelta(hours=2)),
        _make_history(kind, 4, now - timedelta(hours=1)),
    ])
    history_db.flush()
    _, timestamp_name, prune = _history_case(kind)

    prune(history_db, max_entries=2, max_days=3)

    assert _remaining_ids(history_db, kind) == [4, 3]
    model, _, _ = _history_case(kind)
    assert all(
        getattr(row, timestamp_name) >= now - timedelta(days=3)
        for row in history_db.query(model).all()
    )


@pytest.mark.parametrize("kind", ["points", "stock"])
def test_pruning_keeps_callers_transaction_boundary(history_db, kind):
    now = datetime.utcnow()
    history_db.add_all(
        [_make_history(kind, row_id, now - timedelta(minutes=row_id)) for row_id in range(1, 5)]
    )
    history_db.commit()
    _, _, prune = _history_case(kind)

    prune(history_db, max_entries=2, max_days=0)
    assert _remaining_ids(history_db, kind) == [1, 2]

    history_db.rollback()

    assert _remaining_ids(history_db, kind) == [1, 2, 3, 4]
