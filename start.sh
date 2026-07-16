#!/bin/sh
set -e

export TZ="${TZ:-Asia/Shanghai}"

if [ -f "venv/bin/activate" ]; then
    . venv/bin/activate
fi

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"

mkdir -p logs data static/uploads

if [ ! -f "data/database.db" ]; then
    echo "[start] Database not found, initializing..."
    python scripts/init_db.py
else
    echo "[start] Database already exists, skip init."
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5711}"
# Default 1 worker: SQLite + Bark scheduler. Override with UVICORN_WORKERS if needed.
WORKERS="${UVICORN_WORKERS:-1}"

echo "[start] starting uvicorn host=$HOST port=$PORT workers=$WORKERS"
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS" --access-log
