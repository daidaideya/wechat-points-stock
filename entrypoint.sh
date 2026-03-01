#!/bin/sh
set -e

# Initialize database if it doesn't exist
if [ ! -f "data/database.db" ]; then
    echo "Database not found. Initializing..."
    python scripts/init_db.py
else
    echo "Database already exists."
fi

# Create necessary directories
mkdir -p logs data static/uploads

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port 5711 --workers 2 --access-log
