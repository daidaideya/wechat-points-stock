from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from app import timeutil
from app.routers import web


SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")
UTC = timezone.utc


def test_local_date_treats_naive_storage_as_utc_across_shanghai_midnight():
    assert timeutil.local_date(datetime(2025, 1, 1, 15, 59, 59)) == date(2025, 1, 1)
    assert timeutil.local_date(datetime(2025, 1, 1, 16, 0, 0)) == date(2025, 1, 2)
    assert timeutil.local_date(datetime(2025, 1, 1, 16, 0, tzinfo=UTC)) == date(2025, 1, 2)
    assert timeutil.local_date(None) is None


def test_is_same_local_day_handles_exact_midnight_boundary():
    local_now = datetime(2025, 1, 2, 0, 5, tzinfo=SHANGHAI)
    assert timeutil.is_same_local_day(datetime(2025, 1, 1, 16, 1), local_now)
    assert not timeutil.is_same_local_day(datetime(2025, 1, 1, 15, 59, 59), local_now)


def test_unreported_helper_uses_local_day_for_naive_and_offset_timestamps(monkeypatch):
    monkeypatch.setattr(
        timeutil,
        "now_local",
        lambda: datetime(2025, 1, 2, 0, 5, tzinfo=SHANGHAI),
    )

    assert web._is_local_today("2025-01-01T16:01:00")
    assert web._is_local_today("2025-01-02T00:01:00+08:00")
    assert not web._is_local_today("2025-01-01T15:59:59Z")
    assert not web._is_local_today("not-a-timestamp")


def test_stock_change_map_uses_local_business_date_at_midnight(monkeypatch):
    monkeypatch.setattr(
        timeutil,
        "now_local",
        lambda: datetime(2025, 1, 2, 0, 5, tzinfo=SHANGHAI),
    )

    class Query:
        def filter(self, *args, **kwargs):
            return self

        def group_by(self, *args, **kwargs):
            return self

        def all(self):
            return [
                SimpleNamespace(
                    program_id="program-1",
                    product_id="old-product",
                    last_change_time=datetime(2025, 1, 1, 16, 1),
                ),
                SimpleNamespace(
                    program_id="program-1",
                    product_id="new-product",
                    last_change_time=datetime(2025, 1, 1, 16, 2),
                ),
                SimpleNamespace(
                    program_id="program-1",
                    product_id="removed-product",
                    last_change_time=datetime(2025, 1, 1, 15, 59),
                ),
            ]

    class Database:
        def query(self, *args, **kwargs):
            return Query()

    result = web.get_program_stock_change_map(Database(), ["program-1"])

    assert result["program-1"] == {
        "added_count": 2,
        "removed_count": 1,
        "changed": True,
    }
