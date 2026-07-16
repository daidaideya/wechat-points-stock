from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.routers import images, qinglong, stock, web
from app.services import bark_service
from app.services import qinglong_open_service
from app.static_assets import file_response_with_optional_gzip, is_hashed_asset_path

app = FastAPI(title="WeChat Points & Stock Monitor")


@app.on_event("startup")
def _start_background_jobs():
    # Daily Bark push for unreported mini-programs (settings-controlled).
    bark_service.start_bark_scheduler()
    # Periodic QingLong cron enable/disable + schedule mirror (when configured).
    qinglong_open_service.start_qinglong_scheduler()


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
    asset_path = FRONTEND_DIST_DIR / full_path
    if full_path and asset_path.exists() and asset_path.is_file():
        if asset_path.suffix in {".js", ".css", ".svg", ".woff", ".woff2", ".map"}:
            try:
                return file_response_with_optional_gzip(request, asset_path)
            except FileNotFoundError:
                pass
        return FileResponse(asset_path)

    return serve_frontend_index(request)
