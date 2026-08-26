#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

echo "Starting Storyboard Studio at http://${HOST}:${PORT}"
exec python3 -m uvicorn server:app --host "$HOST" --port "$PORT" --reload
