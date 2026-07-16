#!/bin/sh
set -e

# Ensure container wall clock matches China local time even if host/env omitted TZ.
export TZ="${TZ:-Asia/Shanghai}"
if [ -f "/usr/share/zoneinfo/$TZ" ]; then
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime 2>/dev/null || true
    echo "$TZ" > /etc/timezone 2>/dev/null || true
fi

mkdir -p logs data static/uploads

if [ ! -f "data/database.db" ]; then
    echo "[entrypoint] Database not found, initializing..."
    python scripts/init_db.py
else
    echo "[entrypoint] Database already exists, skip init."
fi

if [ ! -f "frontend/dist/index.html" ]; then
    echo "[entrypoint] frontend/dist/index.html not found. Please run npm run build in frontend first."
    exit 1
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5711}"
# SQLite is the default store: keep a single worker unless the operator opts in.
# Multi-worker is supported (WAL + Bark process lock) but not recommended for SQLite.
WORKERS="${UVICORN_WORKERS:-1}"

echo "[entrypoint] starting uvicorn host=$HOST port=$PORT workers=$WORKERS tz=$TZ"
# --proxy-headers helps when reverse-proxied; --timeout-keep-alive keeps browsers warm.
exec uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WORKERS" \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --timeout-keep-alive 15 \
  --access-log
