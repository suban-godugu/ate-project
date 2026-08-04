#!/bin/sh
set -e
PORT="${PORT:-8888}"
# Run ARQ in-process alongside the API (no separate paid Background Worker).
# When the API sleeps on free tier, the worker sleeps too.
arq app.workers.WorkerSettings &
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
