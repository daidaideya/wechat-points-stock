from contextlib import asynccontextmanager
import logging
from pathlib import Path
import re
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.responses import Response

from app.routers import images, qinglong, stock, web
from app.services import bark_service
from app.services import qinglong_open_service
from app.config import settings as app_settings
from app.database import SessionLocal
from app.maintenance import is_database_maintenance
from app.static_assets import file_response_with_optional_gzip, is_hashed_asset_path


@asynccontextmanager
async def lifespan(_app: FastAPI):
    app_settings.validate_runtime()
    # Finish the small compatibility migrations and hot-path indexes before
    # the first browser request, so the stock page does not pay DDL cost.
    db = SessionLocal()
    try:
        web.ensure_runtime_schema(db)
        web.ensure_indexes(db)
    finally:
        db.close()

    try:
        # Daily Bark push for unreported mini-programs (settings-controlled).
        bark_service.start_bark_scheduler()
        # Periodic QingLong cron enable/disable + schedule mirror (when configured).
        qinglong_open_service.start_qinglong_scheduler()
        yield
    finally:
        # Stop both workers even if the other worker's shutdown encounters an
        # error, so every process-owned lock gets a chance to be released.
        try:
            qinglong_open_service.stop_qinglong_scheduler()
        finally:
            bark_service.stop_bark_scheduler()


app = FastAPI(title="WeChat Points & Stock Monitor", lifespan=lifespan)

# Uvicorn configures this logger with the application stderr handler; using a
# child keeps request records visible without installing a second handler or
# duplicating every line when the app is embedded in another server.
request_logger = logging.getLogger("uvicorn.error").getChild("request")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _get_request_id(request: Request) -> str:
    """Return a safe request id without accepting arbitrary log control data."""
    candidate = (request.headers.get("X-Request-ID") or "").strip()
    if _REQUEST_ID_RE.fullmatch(candidate):
        return candidate
    return uuid4().hex


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    """Attach a request id and emit low-cardinality key/value access logs."""
    request_id = _get_request_id(request)
    request.state.request_id = request_id
    started = time.perf_counter()
    path = request.url.path

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - started) * 1000
        # Log only the exception type here. Exception text can contain an
        # upstream URL or payload; request logs must never expose credentials.
        request_logger.error(
            "request_failed request_id=%s method=%s route=%s status=500 duration_ms=%.1f exception=%s",
            request_id,
            request.method,
            path,
            duration_ms,
            type(exc).__name__,
        )
        if path.startswith("/api/") or path.startswith("/health/"):
            return JSONResponse(
                status_code=500,
                content={"detail": "内部服务错误", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )
        raise

    response.headers["X-Request-ID"] = request_id
    if path.startswith("/api/") or path.startswith("/health/"):
        duration_ms = (time.perf_counter() - started) * 1000
        level = logging.WARNING if response.status_code >= 500 else logging.INFO
        request_logger.log(
            level,
            "request_completed request_id=%s method=%s route=%s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            path,
            response.status_code,
            duration_ms,
        )
    return response


@app.get("/health/live", include_in_schema=False)
def health_live():
    return {"status": "ok"}


@app.get("/health/ready", include_in_schema=False)
def health_ready():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database is not ready") from exc
    finally:
        db.close()


# Compress dynamic JSON / HTML on the fly. Hashed assets are served from
# precompressed .gz siblings (see static_assets) and should NOT be re-gzipped.
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def static_and_cache_middleware(request: Request, call_next):
    """Fast path for hashed frontend assets + long cache headers.

    1) Prefer prebuilt `.gz` for /assets/* (skips GZipMiddleware CPU).
    2) Attach immutable cache headers to static/upload responses.
    """
    path = request.url.path

    if is_database_maintenance() and path.startswith("/api/v1/") and path != "/api/v1/settings/database/import":
        return JSONResponse(
            status_code=503,
            content={"detail": "数据库维护中，请稍后重试"},
            headers={"Retry-After": "5"},
        )

    # Serve Vite assets before the rest of the stack when possible.
    if is_hashed_asset_path(path) and FRONTEND_ASSETS_DIR.exists():
        name = path.rsplit("/", 1)[-1]
        # Never expose raw .gz as a navigable asset name without encoding.
        if name.endswith(".gz"):
            return Response(status_code=404)
        asset = FRONTEND_ASSETS_DIR / name
        if asset.is_file():
            try:
                return file_response_with_optional_gzip(request, asset)
            except FileNotFoundError:
                pass

    response = await call_next(request)
    if path.startswith(("/assets/", "/app/assets/", "/static/uploads/")):
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
        if "Content-Encoding" in response.headers:
            response.headers.setdefault("Vary", "Accept-Encoding")
    elif path in ("/", "/app", "/app/") or path.endswith(".html"):
        # index.html must revalidate so new hashed asset names are picked up.
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = Path("/workspace")

STATIC_DIR = BASE_DIR / "static"
if not STATIC_DIR.exists() and (WORKSPACE_DIR / "static").exists():
    STATIC_DIR = WORKSPACE_DIR / "static"

FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
if not FRONTEND_DIST_DIR.exists() and (WORKSPACE_DIR / "frontend" / "dist").exists():
    FRONTEND_DIST_DIR = WORKSPACE_DIR / "frontend" / "dist"

FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"
FRONTEND_DIST_ROOT = FRONTEND_DIST_DIR.resolve()


def resolve_frontend_asset(full_path: str) -> Path | None:
    """Resolve a catch-all SPA path without allowing directory traversal."""
    asset_path = (FRONTEND_DIST_DIR / full_path).resolve()
    try:
        asset_path.relative_to(FRONTEND_DIST_ROOT)
    except ValueError:
        return None
    return asset_path

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Keep mounts as fallback for clients that hit StaticFiles directly; the
# middleware above prefers precompressed responses when available.
if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="frontend-assets")
    app.mount("/app/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="frontend-assets-app")

app.include_router(web.router)
app.include_router(qinglong.router)
app.include_router(stock.router)
app.include_router(images.router)


def serve_frontend_index(request: Request | None = None) -> FileResponse:
    if not FRONTEND_INDEX_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="frontend/dist/index.html not found, please run `npm run build` in frontend",
        )
    headers = {"Cache-Control": "no-cache"}
    return FileResponse(FRONTEND_INDEX_FILE, headers=headers)


@app.get("/", include_in_schema=False)
async def serve_frontend_root(request: Request):
    return serve_frontend_index(request)


@app.get("/app", include_in_schema=False)
async def serve_frontend_app(request: Request):
    return serve_frontend_index(request)


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_routes(full_path: str, request: Request):
    if full_path.startswith(("api/", "static/", "assets/", "docs", "redoc", "openapi.json", "app/routers")):
        raise HTTPException(status_code=404, detail="Not Found")

    # /app/foo SPA paths fall through to index.html
    # The catch-all route must never serve a file outside the built SPA.
    # Encoded `..` segments otherwise could expose .env/database files.
    asset_path = resolve_frontend_asset(full_path)

    if asset_path is not None and full_path and asset_path.exists() and asset_path.is_file():
        if asset_path.suffix in {".js", ".css", ".svg", ".woff", ".woff2", ".map"}:
            try:
                return file_response_with_optional_gzip(request, asset_path)
            except FileNotFoundError:
                pass
        return FileResponse(asset_path)

    return serve_frontend_index(request)
