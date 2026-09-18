import hashlib
import hmac
import time
from secrets import compare_digest
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings

security = HTTPBearer()

ACCESS_SESSION_COOKIE = "site_access_session"
ACCESS_SESSION_TTL_SECONDS = 8 * 60 * 60
_ACCESS_SESSION_VERSION = "v1"


def create_ui_access_session(access_key: str, now: Optional[float] = None) -> str:
    """Create a short-lived, stateless browser session bound to the access key."""
    normalized_key = (access_key or "").strip()
    if not normalized_key:
        raise ValueError("access key is required")

    issued_at = time.time() if now is None else now
    expires_at = int(issued_at + ACCESS_SESSION_TTL_SECONDS)
    payload = f"{_ACCESS_SESSION_VERSION}.{expires_at}"
    signature = hmac.new(
        normalized_key.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def is_valid_ui_access_session(
    session_value: Optional[str],
    access_key: Optional[str],
    now: Optional[float] = None,
) -> bool:
    """Validate the signed browser session without storing server-side state."""
    normalized_key = (access_key or "").strip()
    if not isinstance(session_value, str) or not normalized_key:
        return False

    parts = session_value.split(".")
    if len(parts) != 3 or parts[0] != _ACCESS_SESSION_VERSION:
        return False

    try:
        expires_at = int(parts[1])
    except (TypeError, ValueError):
        return False

    current_time = time.time() if now is None else now
    if expires_at <= int(current_time):
        return False

    payload = f"{parts[0]}.{parts[1]}"
    expected_signature = hmac.new(
        normalized_key.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(parts[2], expected_signature)


def is_valid_ui_access_key(provided_key: Optional[str], stored_key: Optional[str]) -> bool:
    normalized_stored_key = (stored_key or "").strip()
    if not normalized_stored_key:
        return False
    return hmac.compare_digest((provided_key or "").strip(), normalized_stored_key)


def set_ui_access_cookie(response, access_key: str, *, secure: bool = False):
    response.set_cookie(
        key=ACCESS_SESSION_COOKIE,
        value=create_ui_access_session(access_key),
        max_age=ACCESS_SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )


def clear_ui_access_cookie(response):
    response.delete_cookie(ACCESS_SESSION_COOKIE, path="/")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    configured_token = settings.INGEST_TOKEN
    if not configured_token or not compare_digest(token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def require_ui_access(
    request: Request,
    x_access_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
    access_session: Optional[str] = Cookie(default=None, alias=ACCESS_SESSION_COOKIE),
):
    """Protect browser-facing API routes when the UI access lock is enabled.

    Access status and verification are intentionally public so the frontend
    can reach the access gate. All other web/stock routes use this dependency
    at router level; the setting still controls whether the lock is enabled.
    """
    if request.url.path in {"/api/v1/access/status", "/api/v1/access/verify"}:
        return

    # Import lazily to avoid making the dependency module depend on the
    # router/service import graph during application startup.
    from app.services import cleanup_service

    settings_row = cleanup_service.get_or_create_settings(db)
    if settings_row.access_protection_enabled != 1:
        return

    stored_key = (settings_row.access_key or "").strip()
    if not stored_key:
        raise HTTPException(status_code=403, detail="已开启访问保护，但尚未设置访问密钥")
    if is_valid_ui_access_session(access_session, stored_key):
        return
    if not is_valid_ui_access_key(x_access_key, stored_key):
        raise HTTPException(status_code=401, detail="访问密钥错误或未提供")

def get_db_session():
    return get_db()
