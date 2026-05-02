#!/bin/bash
# Start the FastAPI server with the correct Python path
set -e

export PYTHONPATH="$(pwd):$PYTHONPATH"
export PORT="${PORT:-8000}"
export DEBUG="${DEBUG:-false}"

echo "Starting AI Codebase Understanding Engine on port $PORT..."

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers 1 \
    --log-level info
