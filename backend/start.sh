#!/bin/sh
set -e
# Railway public domain is mapped to this listen port (see Networking).
PORT="${PORT:-8888}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
