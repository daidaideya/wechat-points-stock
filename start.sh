#!/bin/sh
set -e

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
WORKERS="${UVICORN_WORKERS:-2}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS" --access-log
