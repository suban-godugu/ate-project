#!/bin/sh
set -e
PORT="${PORT:-8888}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
