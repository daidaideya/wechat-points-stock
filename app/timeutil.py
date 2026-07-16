"""Timezone helpers for consistent China-local wall time in Docker and bare metal.

Project convention for *display* and user-facing schedules (Bark push time,
"today" unreported, ql last sync shown in UI): Asia/Shanghai.

Historical rows often store naive datetimes written via datetime.utcnow().
API serialization always attaches an explicit offset/Z so browsers don't
mis-parse naive ISO strings as local when the container was UTC.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Asia/Shanghai")
UTC = timezone.utc


def now_local() -> datetime:
    """Current wall clock in Asia/Shanghai (tz-aware)."""
    return datetime.now(APP_TZ)


def now_utc() -> datetime:
    return datetime.now(UTC)


def local_today_str() -> str:
    return now_local().strftime("%Y-%m-%d")


def to_aware_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Treat naive values as UTC (historical utcnow writes)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def to_local(dt: Optional[datetime]) -> Optional[datetime]:
    aware = to_aware_utc(dt)
    if aware is None:
        return None
    return aware.astimezone(APP_TZ)


def iso_for_api(dt: Optional[datetime]) -> Optional[str]:
    """Serialize for frontend Date parsing.

    - naive: assumed UTC (legacy utcnow storage) → append Z
    - aware: ISO with offset
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.isoformat(timespec="seconds") + "Z"
    return dt.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def local_display(dt: Optional[datetime]) -> Optional[str]:
    """Human-readable Asia/Shanghai string for settings UI (no ambiguity)."""
    local = to_local(dt)
    if local is None:
        return None
    return local.strftime("%Y-%m-%d %H:%M:%S")


def utcnow_naive() -> datetime:
    """Naive UTC timestamp for DB columns that remain timezone-unaware."""
    return datetime.utcnow()


def local_hhmm() -> str:
    return now_local().strftime("%H:%M")


def is_same_local_day(dt: Optional[datetime], other: Optional[datetime] = None) -> bool:
    if not dt:
        return False
    left = to_local(dt)
    right = to_local(other) if other is not None else now_local()
    if left is None or right is None:
        return False
    return left.date() == right.date()
