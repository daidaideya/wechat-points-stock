"""Serve Vite build assets with optional precompressed .gz siblings.

When `frontend/scripts/gzip-assets.mjs` runs after `vite build`, each large
hashed file has a `.gz` twin. Serving those bytes with Content-Encoding: gzip
avoids Python GZipMiddleware re-compressing ~800KB element-plus on every hit
— a major Docker / low-CPU latency source.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import Request
from fastapi.responses import FileResponse, Response


_ASSET_CACHE = "public, max-age=31536000, immutable"
_HTML_CACHE = "no-cache"


def _content_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed:
        return guessed
    if path.suffix == ".js":
        return "application/javascript"
    if path.suffix == ".css":
        return "text/css"
    if path.suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


def _accepts_gzip(request: Request) -> bool:
    accept = request.headers.get("accept-encoding") or ""
    return "gzip" in accept.lower()


def file_response_with_optional_gzip(
    request: Request,
    file_path: Path,
    *,
    cache_control: Optional[str] = _ASSET_CACHE,
    media_type: Optional[str] = None,
) -> Response:
    """Return FileResponse for `file_path`, preferring `.gz` when available."""
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    ctype = media_type or _content_type(file_path)
    gz_path = Path(str(file_path) + ".gz")
    headers = {}
    if cache_control:
        headers["Cache-Control"] = cache_control

    if _accepts_gzip(request) and gz_path.is_file():
        headers["Content-Encoding"] = "gzip"
        headers["Vary"] = "Accept-Encoding"
        # Serve the .gz file bytes but keep the original content-type (js/css).
        return FileResponse(
            path=str(gz_path),
            media_type=ctype,
            headers=headers,
        )

    return FileResponse(
        path=str(file_path),
        media_type=ctype,
        headers=headers,
    )


def is_hashed_asset_path(path: str) -> bool:
    """True for Vite hashed assets under /assets or /app/assets."""
    return path.startswith(("/assets/", "/app/assets/"))
