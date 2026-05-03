# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A web app for managing WeChat accounts, mini-program points, stock, and sync logs reported from QingLong panel scripts. Backend is FastAPI + SQLAlchemy + SQLite, frontend is Vue 3 + Vite + Element Plus, served as a single bundle. UI strings are Chinese, code identifiers are English.

## Common commands

Backend (run from repo root):

```bash
# Install deps
pip install -r requirements.txt

# Initialize DB (creates data/database.db; safe to re-run)
python scripts/init_db.py

# Dev (port 8000, hot reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Prod-style (port 5711 matches Docker)
uvicorn app.main:app --host 0.0.0.0 --port 5711 --workers 2
```

Frontend (run from `frontend/`):

```bash
npm install
npm run dev        # dev server on :5173, base path /app/
npm run build      # outputs to frontend/dist (required before backend prod start)
npm run analyze    # build + writes frontend/dist/stats.html for bundle inspection
```

Docker (full stack on :5711):

```bash
docker compose up -d --build
```

There is no test suite, linter, or formatter configured. Do not invent commands for them.

## URL and port topology

- Backend dev: `http://127.0.0.1:8000`
- Frontend dev: `http://127.0.0.1:5173/app/` (Vite proxies `/api` and `/static` to :8000)
- Production / Docker: everything on `:5711` (or `:8000` if running uvicorn directly), SPA at `/` and `/app`
- Vue Router uses `createWebHistory('/app/')`, so all SPA URLs are under `/app/...`. Direct backend port without `/app/` still works because `app/main.py` has a catch-all that falls back to `frontend/dist/index.html`.

## Architecture

### Frontend serving and SPA fallback

`app/main.py` mounts three things: `/static` (uploads), `/assets` and `/app/assets` (built JS/CSS), then defines a catch-all `serve_frontend_routes` that returns `frontend/dist/index.html` for any unknown path EXCEPT prefixes `api/`, `static/`, `assets/`, `docs`, `redoc`, `openapi.json`, `app/routers`. If `frontend/dist/index.html` is missing, both `entrypoint.sh` and the runtime endpoints fail loudly. Always build the frontend before starting the backend in production.

`main.py` also has a `/workspace` fallback for `STATIC_DIR` and `FRONTEND_DIST_DIR` to support an alternate mount layout.

### Two independent auth mechanisms

These do different things and should not be confused:

1. **Bearer token** (`API_TOKEN` from `.env`, checked by `app/dependencies.py:verify_token`). Protects QingLong ingest and image upload routers only: `/api/v1/qinglong/*`, `/api/v1/stock-report`, `/api/v1/upload/image`. Used by external scripts (see `scripts/api_template.py`).
2. **Access key** (header `X-Access-Key`, stored in `system_settings.access_key`, gated by `system_settings.access_protection_enabled`). UI-level lock for human users. Enforced manually inside `app/routers/web.py` via `verify_access_or_raise`, only on a few routes (`/api/v1/access/status`, `/api/v1/settings/logs`). Frontend reads/writes it through `frontend/src/api.js` (localStorage key `site_access_key`) and `router.js` redirects to `/access-gate` when needed.

The bulk of `web.py` endpoints are unauthenticated. Adding access-key protection to a new endpoint is opt-in: call `verify_access_or_raise(db, x_access_key, allow_empty_when_disabled=False)` explicitly.

### Schema evolution pattern (no Alembic)

There is no migration framework. Two patterns are used together:

- `Base.metadata.create_all()` in `scripts/init_db.py` for fresh installs.
- Lazy `ensure_*_columns(db)` helpers run at the start of routes to `ALTER TABLE ADD COLUMN` when columns are missing. See `app/routers/web.py:ensure_mini_program_columns`, `app/routers/stock.py:ensure_product_columns`, `app/services/cleanup_service.py:ensure_system_settings_columns`. New nullable columns should follow this pattern so existing `data/database.db` files keep working without manual steps.
- One-off scripts in `scripts/` (e.g. `migrate_add_phone_index.py`, `migrate_note.py` at repo root) for non-column changes like indexes.

When adding a column to an existing model, also add it to the matching `ensure_*_columns` map.

### QingLong points ingest: phone number detour

`app/services/qinglong_service.py:process_points_report` has nontrivial behavior keyed on `wechat_id` shape:

- If `wechat_id` matches `^1[3-9]\d{9}$` (Chinese mobile): the nickname in the request body is ignored. If a `WechatAccount` exists with that `phone`, its existing nickname is reused; otherwise nickname is forced to empty string.
- Otherwise: caller-supplied `nickname` is honored.

Stock and points history both call `cleanup_service.prune_*_history` after each ingest, governed by `system_settings.max_log_entries` / `max_retention_days`.

### Frontend build configuration

`frontend/vite.config.js` matters for two reasons that affect how new code should be written:

- `unplugin-auto-import` injects Vue and Vue Router APIs (`ref`, `computed`, `useRoute`, ...) globally. Do not add explicit `import { ref } from 'vue'`; auto-import generates `src/auto-imports.d.ts`.
- `unplugin-vue-components` + `ElementPlusResolver` auto-registers Element Plus components and per-component CSS. Do not register Element Plus globally in `main.js` and do not import `element-plus/dist/index.css`. Icons from `@element-plus/icons-vue` still need explicit per-file imports.
- `manualChunks` splits `element-plus`, `@element-plus/icons-vue`, `vue`, `vue-router`, `axios` into separate vendor chunks. Adding new heavy deps may warrant extending this list.

### Program search uses pinyin

`GET /api/v1/programs?q=...` in `web.py` runs Chinese pinyin matching (full pinyin and first-letter initials via `pypinyin`) for datasets under 2000 programs; above that it falls back to plain `LIKE`. Keep this in mind before changing the search code path.

## Key files for navigation

- `app/main.py`: app wiring, static mounts, SPA fallback.
- `app/routers/web.py`: most UI-facing endpoints (dashboard, accounts, programs, points, settings, access).
- `app/routers/stock.py`: stock management and product CRUD.
- `app/routers/qinglong.py` + `app/services/qinglong_service.py`: external ingest from QingLong scripts.
- `app/services/cleanup_service.py`: settings accessor and history pruning.
- `app/models.py`: SQLAlchemy models. Note `is_favorite`, `is_hidden`, `access_protection_enabled` are `Integer` (0/1), not boolean.
- `frontend/src/router.js`: route table, also drives the access-gate redirect.
- `frontend/src/api.js`: axios instance with `/api/v1` baseURL and `X-Access-Key` injection.
- `scripts/api_template.py`: reference client for QingLong scripts that report points.

## Persisted state

- `data/database.db`: SQLite (gitignored).
- `static/uploads/`: uploaded product images, served at `/static/uploads/...`.
- `logs/`: runtime logs.
- `frontend/dist/`: built SPA, required at runtime.

In `docker-compose.yml` these four directories plus `app/` and `scripts/` are bind-mounted, so code edits on the host reflect into the container without rebuild (uvicorn is not run with `--reload` in the container, restart needed).
