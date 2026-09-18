from secrets import compare_digest
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings

security = HTTPBearer()

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
    provided_key = (x_access_key or "").strip()
    if not stored_key:
        raise HTTPException(status_code=403, detail="已开启访问保护，但尚未设置访问密钥")
    if not compare_digest(provided_key, stored_key):
        raise HTTPException(status_code=401, detail="访问密钥错误或未提供")

def get_db_session():
    return get_db()
