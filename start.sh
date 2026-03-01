#!/bin/bash
# start.sh

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p static/uploads

# Start server
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 5711 \
    --workers 2 \
    --access-log
