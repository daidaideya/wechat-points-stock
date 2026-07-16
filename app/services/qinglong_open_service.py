"""QingLong panel OpenAPI client — read-only cron enable/disable sync.

Auth: GET {base}/open/auth/token?client_id=&client_secret=
Crons: GET {base}/open/crons  Authorization: Bearer <token>
Cron isDisabled: 0 = enabled, 1 = disabled
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from app import models
from app.services import cleanup_service

# In-process token cache: key -> (token, expire_unix)
_TOKEN_CACHE: Dict[str, Tuple[str, float]] = {}

_STRIP_PREFIXES = (
    "code版_",
    "code版",
    "code_",
    "task ",
    "python3 ",
    "python ",
    "node ",
    "ql ",
)
_STRIP_SUFFIXES = (
    "签到",
    "自动任务",
    "任务",
    "脚本",
    ".py",
    ".js",
    ".ts",
)


def _normalize_name(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).strip().lower()
    for prefix in _STRIP_PREFIXES:
        if text.startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    for suffix in _STRIP_SUFFIXES:
        if text.endswith(suffix.lower()):
            text = text[: -len(suffix)].strip()
    # Drop path separators / task wrappers noise
    text = text.replace("\\", "/").split("/")[-1]
    text = re.sub(r"[\s_\-·•]+", "", text)
    return text


def _command_stem(command: Optional[str]) -> str:
    if not command:
        return ""
    # e.g. "task code版_可口可乐吧.py" / "python3 /ql/scripts/foo.py"
    parts = str(command).strip().split()
    candidate = parts[-1] if parts else str(command)
    candidate = candidate.replace("\\", "/").split("/")[-1]
    return _normalize_name(candidate)


def _cache_key(base_url: str, client_id: str) -> str:
    return f"{base_url.rstrip('/')}|{client_id}"


def get_token(base_url: str, client_id: str, client_secret: str, force_refresh: bool = False) -> str:
    base = base_url.rstrip("/")
    key = _cache_key(base, client_id)
    now = time.time()
    if not force_refresh and key in _TOKEN_CACHE:
        token, exp = _TOKEN_CACHE[key]
        if token and exp > now + 60:
            return token

    url = f"{base}/open/auth/token"
    resp = requests.get(
        url,
        params={"client_id": client_id, "client_secret": client_secret},
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise RuntimeError(body.get("message") or f"QingLong auth failed: {body}")
    data = body.get("data") or {}
    token = data.get("token")
    if not token:
        raise RuntimeError("QingLong auth response missing token")
    expiration = data.get("expiration")
    if isinstance(expiration, (int, float)) and expiration > now:
        exp = float(expiration)
    else:
        exp = now + 30 * 24 * 3600
    _TOKEN_CACHE[key] = (token, exp)
    return token


def list_crons(base_url: str, token: str) -> List[Dict[str, Any]]:
    base = base_url.rstrip("/")
    url = f"{base}/open/crons"
    headers = {"Authorization": f"Bearer {token}"}
    # page/size 0 → full list in current QL versions
    resp = requests.get(url, headers=headers, params={"page": 0, "size": 0}, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise RuntimeError(body.get("message") or f"QingLong list crons failed: {body}")
    data = body.get("data")
    if isinstance(data, dict):
        rows = data.get("data") or []
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    return rows


def _match_score(program_name: str, cron: Dict[str, Any]) -> int:
    """Higher is better. 0 = no match."""
    prog = _normalize_name(program_name)
    if not prog:
        return 0
    cron_name = _normalize_name(cron.get("name"))
    cmd_stem = _command_stem(cron.get("command"))

    if cron_name and cron_name == prog:
        return 1000 + len(cron_name)
    if cmd_stem and cmd_stem == prog:
        return 900 + len(cmd_stem)
    # containment: prefer longer overlap
    if cron_name and (cron_name in prog or prog in cron_name):
        return 500 + min(len(cron_name), len(prog))
    if cmd_stem and (cmd_stem in prog or prog in cmd_stem):
        return 400 + min(len(cmd_stem), len(prog))
    return 0


def match_crons_to_programs(
    programs: List[models.MiniProgram],
    crons: List[Dict[str, Any]],
) -> Dict[int, Dict[str, Any]]:
    """Return map program.id -> best matching cron dict."""
    result: Dict[int, Dict[str, Any]] = {}
    used_cron_ids = set()

    # Score all pairs, assign greedily best-first to avoid one cron claiming many
    pairs: List[Tuple[int, int, int, Dict[str, Any]]] = []
    for program in programs:
        for cron in crons:
            score = _match_score(program.program_name or "", cron)
            if score <= 0:
                # also try program_id as last resort (rare)
                score = _match_score(program.program_id or "", cron)
            if score > 0:
                pairs.append((score, program.id, cron.get("id"), cron))

    pairs.sort(key=lambda x: (-x[0], -len(str(x[3].get("name") or ""))))
    claimed_programs = set()
    for score, program_id, cron_id, cron in pairs:
        if program_id in claimed_programs:
            continue
        if cron_id is not None and cron_id in used_cron_ids:
            continue
        claimed_programs.add(program_id)
        if cron_id is not None:
            used_cron_ids.add(cron_id)
        result[program_id] = cron
    return result


def sync_cron_status(db: Session) -> Dict[str, Any]:
    """Pull QingLong crons and mirror enable/disable onto mini_programs."""
    cleanup_service.ensure_system_settings_columns(db)
    # ensure mini program ql columns via web helper would create circular import;
    # columns are ensured by web routes before list/sync endpoints call us.
    settings = cleanup_service.get_or_create_settings(db)
    base_url = (settings.ql_base_url or "").strip()
    client_id = (settings.ql_client_id or "").strip()
    client_secret = (settings.ql_client_secret or "").strip()

    if not base_url or not client_id or not client_secret:
        settings.ql_last_sync_at = datetime.utcnow()
        settings.ql_last_sync_status = "未配置青龙 OpenAPI（需要 URL / Client ID / Client Secret）"
        db.add(settings)
        db.commit()
        return {
            "status": "skipped",
            "message": settings.ql_last_sync_status,
            "matched": 0,
            "total_programs": 0,
            "total_crons": 0,
        }

    try:
        token = get_token(base_url, client_id, client_secret)
        crons = list_crons(base_url, token)
        programs = db.query(models.MiniProgram).all()
        matches = match_crons_to_programs(programs, crons)
        now = datetime.utcnow()
        matched_count = 0

        for program in programs:
            cron = matches.get(program.id)
            if not cron:
                program.ql_cron_id = None
                program.ql_cron_name = None
                program.ql_is_disabled = None
                program.ql_matched_at = now
                program.ql_command = None
                program.ql_schedule = None
                db.add(program)
                continue

            matched_count += 1
            is_disabled = cron.get("isDisabled")
            try:
                is_disabled_int = int(is_disabled) if is_disabled is not None else 0
            except (TypeError, ValueError):
                is_disabled_int = 0

            schedule = cron.get("schedule")
            if schedule is not None:
                schedule = str(schedule).strip()[:100] or None

            program.ql_cron_id = cron.get("id")
            program.ql_cron_name = cron.get("name")
            program.ql_is_disabled = is_disabled_int
            program.ql_matched_at = now
            program.ql_command = (cron.get("command") or "")[:500] or None
            program.ql_schedule = schedule
            db.add(program)

        settings.ql_last_sync_at = now
        settings.ql_last_sync_status = (
            f"ok: matched {matched_count}/{len(programs)} programs, {len(crons)} crons"
        )
        db.add(settings)
        db.commit()
        return {
            "status": "success",
            "message": settings.ql_last_sync_status,
            "matched": matched_count,
            "total_programs": len(programs),
            "total_crons": len(crons),
            "synced_at": now.isoformat(),
        }
    except Exception as exc:
        settings.ql_last_sync_at = datetime.utcnow()
        settings.ql_last_sync_status = f"error: {exc}"
        db.add(settings)
        db.commit()
        return {
            "status": "error",
            "message": str(exc),
            "matched": 0,
            "total_programs": 0,
            "total_crons": 0,
        }


def maybe_auto_sync(db: Session, min_interval_minutes: int = 10) -> None:
    """Best-effort background refresh; never raises to caller."""
    try:
        settings = cleanup_service.get_or_create_settings(db)
        if not (settings.ql_base_url and settings.ql_client_id and settings.ql_client_secret):
            return
        last = settings.ql_last_sync_at
        if last and (datetime.utcnow() - last) < timedelta(minutes=min_interval_minutes):
            return
        sync_cron_status(db)
    except Exception as exc:
        print(f"[qinglong_open_service] auto sync failed: {exc}")
