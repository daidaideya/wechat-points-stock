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

Docker (full stack on :5711). Build SPA first — entrypoint requires `frontend/dist/index.html`:

```bash
cd frontend && npm run build && cd ..
docker compose up -d --build
```

Docker notes for this project:

- Default `UVICORN_WORKERS=1` (SQLite). Multi-worker works with WAL + Bark file lock but is not recommended.
- Compose adds `host.docker.internal:host-gateway` so QingLong on the host is reachable as `http://host.docker.internal:5700`.
- Volumes: `data`, `logs`, `static/uploads`, `frontend/dist`, plus bind-mounted `app/` and `scripts/`.
- SQLite enables `PRAGMA journal_mode=WAL` and `busy_timeout=5000` on connect for safer concurrent readers.

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
2. **Access key** (header `X-Access-Key`, stored in `system_settings.access_key`, gated by `system_settings.access_protection_enabled`). UI-level lock for human users. Enforced manually inside `app/routers/web.py` via `verify_access_or_raise` on settings/access routes (logs, qinglong, bark, database backup). Frontend reads/writes it through `frontend/src/api.js` (localStorage key `site_access_key`) and `router.js` redirects to `/access-gate` when needed.

The bulk of `web.py` endpoints are unauthenticated. Adding access-key protection to a new endpoint is opt-in: call `verify_access_or_raise(db, x_access_key, allow_empty_when_disabled=False)` explicitly.

### Schema evolution pattern (no Alembic)

There is no migration framework. Two patterns are used together:

- `Base.metadata.create_all()` in `scripts/init_db.py` for fresh installs.
- Lazy `ensure_*_columns(db)` helpers run at the start of routes to `ALTER TABLE ADD COLUMN` when columns are missing. See `app/routers/web.py:ensure_mini_program_columns`, `app/routers/stock.py:ensure_product_columns`, `app/services/cleanup_service.py:ensure_system_settings_columns` / `ensure_points_history_columns`. New nullable columns should follow this pattern so existing `data/database.db` files keep working without manual steps.
- One-off scripts in `scripts/` (e.g. `migrate_add_phone_index.py`, `migrate_note.py` at repo root) for non-column changes like indexes.

When adding a column to an existing model, also add it to the matching `ensure_*_columns` map.

### QingLong points ingest: points + optional cash

`POST /api/v1/qinglong/report` body item (`ProgramPointsData`):

- `current_points` optional float
- `current_cash` optional float (yuan)
- **at least one of the two is required**
- Old scripts that only send `current_points` remain compatible
- Missing dimension is stored as SQL `NULL` (not 0)

`app/services/qinglong_service.py:process_points_report` still has phone-number nickname logic:

- If `wechat_id` matches `^1[3-9]\d{9}$` (Chinese mobile): the nickname in the request body is ignored. If a `WechatAccount` exists with that `phone`, its existing nickname is reused; otherwise nickname is forced to empty string.
- Otherwise: caller-supplied `nickname` is honored.

Stock and points history both call `cleanup_service.prune_*_history` after each ingest, governed by `system_settings.max_log_entries` / `max_retention_days`.

### QingLong OpenAPI sync (read-only)

`app/services/qinglong_open_service.py` syncs cron enable/disable + schedule into `mini_programs.ql_*` fields:

- Auth: `GET {base}/open/auth/token?client_id=&client_secret=`
- List: `GET {base}/open/crons`
- Match primarily by cron task name ↔ `program_name` (with command basename fallback)
- Settings: `/api/v1/settings/qinglong` + `/sync`
- **Auto-refresh** (no manual click required once configured):
  - Interval is user-configurable: `system_settings.ql_auto_sync_minutes` (default 5, range 1–1440) via Settings UI
  - Startup scheduler re-reads that interval each cycle (`start_qinglong_scheduler` from `main.py`)
  - `GET /api/v1/programs` kicks a **non-blocking** background sync if last sync is older than the configured interval
  - Multi-worker safe via file lock under `data/.qinglong_scheduler.lock` + in-process inflight guard
  - Manual「立即同步」 still available for instant refresh
- Timezone: app treats display/schedules as **Asia/Shanghai**. Docker image sets `TZ` + `/etc/localtime`; API timestamps for settings use explicit `Z` (`app/timeutil.iso_for_api`) so browser local display is correct even if the container was once UTC.

### Bark unreported push

`app/services/bark_service.py` starts a daemon scheduler from `app/main.py` startup:

- Settings: `/api/v1/settings/bark` + `/test`
- When enabled, at local `bark_push_time` (default `20:00`) pushes today's unreported active programs to Bark
- Manual test always allowed even if auto-push is disabled

### Program list query notes

`GET /api/v1/programs` supports:

- `q` pinyin/name search (pypinyin under 2000 programs, else `LIKE`)
- `status` active/archived/all
- `ql_status` all/enabled/disabled/unknown
- `sort` default | cron (earliest daily cron minute from `ql_schedule`)

### Frontend build configuration

`frontend/vite.config.js` matters for two reasons that affect how new code should be written:

- `unplugin-auto-import` injects Vue and Vue Router APIs (`ref`, `computed`, `useRoute`, ...) globally. Do not add explicit `import { ref } from 'vue'`; auto-import generates `src/auto-imports.d.ts`.
- `unplugin-vue-components` + `ElementPlusResolver` auto-registers Element Plus components and per-component CSS. Do not register Element Plus globally in `main.js` and do not import `element-plus/dist/index.css`. Icons from `@element-plus/icons-vue` still need explicit per-file imports.
- `manualChunks` splits `element-plus`, `@element-plus/icons-vue`, `vue`, `vue-router`, `axios` into separate vendor chunks. Adding new heavy deps may warrant extending this list.
- `npm run build` also runs `scripts/gzip-assets.mjs`, writing `*.js.gz` / `*.css.gz` next to hashed assets. `app/static_assets.py` + middleware in `main.py` serve those with `Content-Encoding: gzip` so Docker/Python does not re-gzip 800KB+ JS on every request.

### Mobile navigation

Do **not** use Element Plus `el-drawer` for the main mobile nav. `App.vue` uses an in-layout custom shell (`.mobile-nav-shell`) so desktop↔mobile resize does not leave click-blocking overlays.

## Key files for navigation

- `app/main.py`: app wiring, static mounts, SPA fallback, Bark scheduler startup.
- `app/routers/web.py`: most UI-facing endpoints (dashboard, accounts, programs, points, settings, access, bark, db backup).
- `app/routers/stock.py`: stock management and product CRUD.
- `app/routers/qinglong.py` + `app/services/qinglong_service.py`: external ingest from QingLong scripts.
- `app/services/qinglong_open_service.py`: QingLong OpenAPI cron status sync.
- `app/services/bark_service.py`: Bark scheduled/manual unreported push.
- `app/services/cleanup_service.py`: settings accessor, lazy column ensure, history pruning.
- `app/models.py`: SQLAlchemy models. Note `is_favorite`, `is_hidden`, `access_protection_enabled`, `bark_enabled`, `ql_is_disabled` are `Integer` (0/1), not boolean. `PointsHistory.points/cash` are nullable floats.
- `frontend/src/router.js`: route table, also drives the access-gate redirect.
- `frontend/src/api.js`: axios instance with `/api/v1` baseURL and `X-Access-Key` injection.
- `frontend/src/views/ProgramsPage.vue`: main program cards UI (filters, stock/detail dialogs, cron sort).
- `frontend/src/views/SettingsPage.vue`: sectioned settings (general / qinglong / bark / database).
- `scripts/api_template.py`: reference client for QingLong scripts that report points/cash.

## Persisted state

- `data/database.db`: SQLite (gitignored).
- `static/uploads/`: uploaded product images, served at `/static/uploads/...`.
- `logs/`: runtime logs.
- `frontend/dist/`: built SPA, required at runtime.

In `docker-compose.yml` these four directories plus `app/` and `scripts/` are bind-mounted, so code edits on the host reflect into the container without rebuild (uvicorn is not run with `--reload` in the container, restart needed).
