"""Bark push for daily unreported mini-programs.

Config lives in system_settings. A lightweight background thread checks every
minute whether the configured local time has arrived and whether today's push
has already been sent.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TextIO
from urllib.parse import quote

import requests
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.services import cleanup_service

_DEFAULT_SERVER = "https://api.day.app"
_DEFAULT_PUSH_TIME = "20:00"
_scheduler_started = False
_scheduler_lock = threading.Lock()
# Cross-process lock so multi-worker uvicorn (Docker default used to be 2)
# only runs one Bark scheduler instance.
_process_lock_fh: Optional[TextIO] = None
_PROCESS_LOCK_PATH = os.path.join("data", ".bark_scheduler.lock")


def normalize_push_time(value: Optional[str]) -> str:
    text = (value or "").strip()
    if not text:
        return _DEFAULT_PUSH_TIME
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return _DEFAULT_PUSH_TIME
        return f"{hour:02d}:{minute:02d}"
    except Exception:
        return _DEFAULT_PUSH_TIME


def normalize_server(value: Optional[str]) -> str:
    text = (value or "").strip().rstrip("/")
    return text or _DEFAULT_SERVER


def list_unreported_programs(db: Session) -> List[models.MiniProgram]:
    """Active (non-archived) programs with no points report today (local date)."""
    programs = (
        db.query(models.MiniProgram)
        .filter(
            (models.MiniProgram.is_archived == 0) | (models.MiniProgram.is_archived.is_(None))
        )
        .order_by(models.MiniProgram.sort_order.desc(), models.MiniProgram.id.asc())
        .all()
    )
    if not programs:
        return []

    program_ids = [p.program_id for p in programs]
    from sqlalchemy import func

    rows = (
        db.query(
            models.PointsHistory.program_id,
            func.max(models.PointsHistory.report_time),
        )
        .filter(models.PointsHistory.program_id.in_(program_ids))
        .group_by(models.PointsHistory.program_id)
        .all()
    )
    last_map = {row[0]: row[1] for row in rows}
    from app.timeutil import is_same_local_day, local_today_str

    today_str = local_today_str()

    unreported = []
    for program in programs:
        last_time = last_map.get(program.program_id)
        if not last_time:
            unreported.append(program)
            continue
        # Compare by Asia/Shanghai calendar day (handles Docker UTC containers).
        if not is_same_local_day(last_time):
            unreported.append(program)
    return unreported


def build_unreported_message(programs: List[models.MiniProgram], limit: int = 20) -> Dict[str, str]:
    count = len(programs)
    title = f"今日未报小程序 {count} 个"
    if count == 0:
        body = "全部活跃小程序今日均已上报。"
        return {"title": title, "body": body}

    names = []
    for program in programs[:limit]:
        names.append(program.program_name or program.program_id)
    body = "、".join(names)
    if count > limit:
        body += f" 等共 {count} 个"
    return {"title": title, "body": body}


def send_bark_push(
    server: str,
    device_key: str,
    title: str,
    body: str,
    group: str = "库存监控",
) -> Dict[str, Any]:
    base = normalize_server(server)
    key = (device_key or "").strip()
    if not key:
        raise ValueError("Bark Device Key 未配置")

    # Official style: GET/POST https://api.day.app/{key}/{title}/{body}
    url = f"{base}/{quote(key, safe='')}/{quote(title or '通知', safe='')}/{quote(body or '', safe='')}"
    resp = requests.get(
        url,
        params={"group": group, "isArchive": "1"},
        timeout=15,
    )
    resp.raise_for_status()
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    # Bark success usually code == 200
    code = data.get("code") if isinstance(data, dict) else None
    if code not in (None, 200, "200"):
        raise RuntimeError(data.get("message") or f"Bark 返回异常: {data}")
    return data if isinstance(data, dict) else {"raw": data}


def push_unreported_now(db: Session, force: bool = False) -> Dict[str, Any]:
    settings = cleanup_service.get_or_create_settings(db)
    enabled = int(getattr(settings, "bark_enabled", 0) or 0) == 1
    if not enabled and not force:
        return {"status": "skipped", "message": "Bark 推送未启用"}

    server = normalize_server(getattr(settings, "bark_server", None))
    device_key = (getattr(settings, "bark_device_key", None) or "").strip()
    if not device_key:
        settings.bark_last_push_at = datetime.utcnow()
        settings.bark_last_push_status = "error: 未配置 Device Key"
        db.add(settings)
        db.commit()
        return {"status": "error", "message": "未配置 Bark Device Key"}

    programs = list_unreported_programs(db)
    message = build_unreported_message(programs)
    try:
        result = send_bark_push(
            server=server,
            device_key=device_key,
            title=message["title"],
            body=message["body"],
        )
        settings.bark_last_push_at = datetime.utcnow()
        settings.bark_last_push_status = f"ok: {message['title']}"
        db.add(settings)
        db.commit()
        return {
            "status": "success",
            "message": settings.bark_last_push_status,
            "count": len(programs),
            "title": message["title"],
            "body": message["body"],
            "bark": result,
        }
    except Exception as exc:
        settings.bark_last_push_at = datetime.utcnow()
        settings.bark_last_push_status = f"error: {exc}"
        db.add(settings)
        db.commit()
        return {"status": "error", "message": str(exc), "count": len(programs)}


def _already_pushed_today(settings: models.SystemSettings) -> bool:
    last = getattr(settings, "bark_last_push_at", None)
    if not last:
        return False
    try:
        from app.timeutil import is_same_local_day

        return is_same_local_day(last) and str(settings.bark_last_push_status or "").startswith("ok:")
    except Exception:
        return False


def maybe_run_scheduled_push() -> None:
    db = SessionLocal()
    try:
        settings = cleanup_service.get_or_create_settings(db)
        if int(getattr(settings, "bark_enabled", 0) or 0) != 1:
            return
        if not (getattr(settings, "bark_device_key", None) or "").strip():
            return

        push_time = normalize_push_time(getattr(settings, "bark_push_time", None))
        # Asia/Shanghai wall clock so Docker without TZ still matches user schedule.
        from app.timeutil import local_hhmm

        current = local_hhmm()
        if current != push_time:
            return
        if _already_pushed_today(settings):
            return
        push_unreported_now(db, force=False)
    except Exception as exc:
        print(f"[bark_service] scheduled push failed: {exc}")
    finally:
        db.close()


def _scheduler_loop():
    # Align roughly to minute boundaries
    while True:
        try:
            maybe_run_scheduled_push()
        except Exception as exc:
            print(f"[bark_service] loop error: {exc}")
        # sleep until next minute + small offset
        now = time.time()
        delay = 60 - (now % 60) + 1
        time.sleep(max(5, min(delay, 60)))


def _try_acquire_process_lock(path: str = _PROCESS_LOCK_PATH) -> bool:
    """Non-blocking exclusive lock across processes (fcntl on Linux, msvcrt on Windows)."""
    global _process_lock_fh
    if _process_lock_fh is not None:
        return True

    lock_dir = os.path.dirname(path) or "."
    try:
        os.makedirs(lock_dir, exist_ok=True)
    except OSError as exc:
        print(f"[bark_service] cannot create lock dir {lock_dir}: {exc}")
        return False

    try:
        fh = open(path, "a+", encoding="utf-8")
    except OSError as exc:
        print(f"[bark_service] cannot open lock file {path}: {exc}")
        return False

    try:
        if os.name == "nt":
            import msvcrt

            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        fh.seek(0)
        fh.truncate()
        fh.write(str(os.getpid()))
        fh.flush()
        _process_lock_fh = fh
        return True
    except (OSError, BlockingIOError, PermissionError) as exc:
        try:
            fh.close()
        except OSError:
            pass
        print(f"[bark_service] another process holds scheduler lock ({exc})")
        return False


def start_bark_scheduler() -> None:
    """Start daily Bark checker once per container/host, not once per uvicorn worker."""
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        if not _try_acquire_process_lock():
            print("[bark_service] scheduler skipped (another worker already owns it)")
            return
        thread = threading.Thread(target=_scheduler_loop, name="bark-scheduler", daemon=True)
        thread.start()
        _scheduler_started = True
        print("[bark_service] scheduler started")
