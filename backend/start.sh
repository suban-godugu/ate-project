#!/bin/sh
set -e
PORT="${PORT:-8888}"
# Free Render is 512MB. Running ARQ + uvicorn in one box OOMs on STIL parses and
# restarts in a death loop (retry delayed parse_upload → OOM → restart).
# Opt-in: set ENABLE_INLINE_WORKER=1 on Render only when you have 2GB+ RAM
# or after clearing stuck jobs and using PARSER_LIGHT_MODE.
if [ "${ENABLE_INLINE_WORKER:-0}" = "1" ]; then
  arq app.workers.WorkerSettings &
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
