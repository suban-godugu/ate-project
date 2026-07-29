# Scan Chain Pipeline — Production Deployment

## Dependencies

- PostgreSQL, Redis, MinIO (existing compose)
- Backend API + ARQ worker
- Pattern Agent `:8010`
- Failure Agent API `:8020`
- Scan Diagnosis `:8030`
- Parser Engine at `PARSER_ENGINE_PATH` (default `C:\personal\parser engine`)

## Environment

```env
DATABASE_URL=postgresql+asyncpg://verilumen:verilumen@localhost:5432/verilumen
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
PATTERN_AGENT_BASE_URL=http://127.0.0.1:8010
FAILURE_AGENT_API_URL=http://127.0.0.1:8020
SCAN_DIAGNOSIS_AGENT_API_URL=http://127.0.0.1:8030
VERILUMEN_SERVICE_KEY=dev-service-key-change-me
PARSER_ENGINE_PATH=C:\personal\parser engine
AGENT_HTTP_TIMEOUT_SEC=120
AGENT_HTTP_RETRIES=3
```

Agents must set the same `VERILUMEN_SERVICE_KEY`.

## Migrate

```bash
cd Backend-and-DP-s-main
alembic upgrade head
pip install -r requirements.txt
pip install -e "C:\personal\parser engine"
pip install httpx
```

## Run

```bash
# API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Worker (parse + orchestrate)
arq app.workers.WorkerSettings

# Agents (separate terminals)
# Pattern :8010, Failure :8020, Scan Diagnosis :8030
```

## Scale-out

- Run multiple ARQ workers against the same Redis.
- Dataset URIs are MinIO presigned GETs (2h) so agents need network access to MinIO.
- Keep parse and orchestrate on the same queue initially; split queues later if needed.

## Health

- Backend `/api/v1/integrations/*-agent/health`
- Agent pipeline routes: Pattern `/api/pipeline/consume`, Failure `/api/v1/pipeline/consume`, Scan `/api/v1/pipeline/consume`

## Failure / retry

- Failed stage published on SSE + `error_message` on `upload_jobs`
- `POST /api/v1/retry/{id}` with optional `{ "stage": "running_pattern" }`
- Parse-stage failures re-enqueue `parse_upload`; agent-stage failures re-enqueue `orchestrate_agents`
