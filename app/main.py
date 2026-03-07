from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import images, qinglong, stock, web

app = FastAPI(title="WeChat Points & Stock Monitor")

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

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="frontend-assets")
    app.mount("/app/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="frontend-assets-app")

app.include_router(web.router)
app.include_router(qinglong.router)
app.include_router(stock.router)
app.include_router(images.router)


def serve_frontend_index() -> FileResponse:
    if not FRONTEND_INDEX_FILE.exists():
        raise HTTPException(status_code=503, detail="frontend/dist/index.html not found, please run `npm run build` in frontend")
    return FileResponse(FRONTEND_INDEX_FILE)


@app.get("/", include_in_schema=False)
async def serve_frontend_root():
    return serve_frontend_index()


@app.get("/app", include_in_schema=False)
async def serve_frontend_app():
    return serve_frontend_index()


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend_routes(full_path: str):
    if full_path.startswith(("api/", "static/", "assets/", "docs", "redoc", "openapi.json", "app/routers")):
        raise HTTPException(status_code=404, detail="Not Found")

    asset_path = FRONTEND_DIST_DIR / full_path
    if full_path and asset_path.exists() and asset_path.is_file():
        return FileResponse(asset_path)

    return serve_frontend_index()
