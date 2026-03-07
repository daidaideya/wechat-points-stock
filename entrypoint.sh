#!/bin/sh
set -e

mkdir -p logs data static/uploads

if [ ! -f "data/database.db" ]; then
    echo "[entrypoint] Database not found, initializing..."
    python scripts/init_db.py
else
    echo "[entrypoint] Database already exists, skip init."
fi

if [ ! -f "frontend/dist/index.html" ]; then
    echo "[entrypoint] frontend/dist/index.html not found. Image may be built incorrectly."
    exit 1
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5711}"
WORKERS="${UVICORN_WORKERS:-2}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS" --access-log
