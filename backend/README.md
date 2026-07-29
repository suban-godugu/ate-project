# VERILUMEN Backend

> **Repository:** [Verilumen-Labss/Backend-and-DP-s](https://github.com/Verilumen-Labss/Backend-and-DP-s) · Owner: suban@verilumen.ai (suban-godugu)

FastAPI backend for the VERILUMEN semiconductor test intelligence platform. Structured data lives in **PostgreSQL**, files in **MinIO**, and cache/sessions/job status in **Redis**.

Companion frontend: [Verilumen-ai/dashboard](https://github.com/Verilumen-ai/dashboard) (Next.js).

---

---

## Quick Start (native Windows, no Docker)

### 1. Install local services

```powershell
cd backend
Copy-Item .env.example .env
```

Install and start these natively on Windows:

- **PostgreSQL** `:5432`
- **Redis** `:6379`
- **MinIO** `:9000` (console `:9001`)

See [`NATIVE_WINDOWS_SETUP.md`](./NATIVE_WINDOWS_SETUP.md) for the full setup and startup sequence.

### 2. Python setup (first time)

```powershell
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
```

Seed user: `alex@verilumen.ai` / `changeme123`

### 3. Run API + worker (local dev, separate terminals)

```powershell
# Terminal A — API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal B — background jobs
arq app.workers.WorkerSettings
```

Health: [http://localhost:8000/health](http://localhost:8000/health)  
API base: `http://localhost:8000/api/v1`

### 4. Connect the dashboard

In `../dashboard/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_MODE=live
```

Restart frontend (`npm run dev`), sign in at `/login`.

---

## Contents

- [Architecture](#architecture)
- [Data placement rules](#data-placement-rules)
- [Project layout](#project-layout)
- [Database schema](#database-schema)
- [API endpoints](#api-endpoints)
- [Redis cache keys](#redis-cache-keys)
- [MinIO object keys](#minio-object-keys)
- [Docker services](#docker-services)
- [Environment variables](#environment-variables)
- [Implementation status & gaps](#implementation-status--gaps)
- [Prompt documentation (CSV)](#prompt-documentation-csv)
- [Production checklist](#production-checklist)

---

## Architecture

```text
┌─────────────────┐     HTTP/SSE      ┌──────────────────┐
│  Next.js        │ ────────────────► │  FastAPI :8000   │
│  dashboard :3000│ ◄──────────────── │  /api/v1/*       │
└─────────────────┘     JWT Bearer    └────────┬─────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
             PostgreSQL :5432           Redis :6379                 MinIO :9000
             (structured data)          (cache, sessions,           (STDF, logs,
                                        job status, SSE)             images, PDFs)
                                               │
                                               ▼
                                        ARQ worker
                                        parse_upload
                                        run_primary_action
                                        run_ai_diagnosis
```

---

## Data placement rules

| Data shape | Store |
|---|---|
| Needs JOINs, filtering, pagination, audit trail | **PostgreSQL** |
| File or blob > ~100KB | **MinIO** (Postgres stores only `object_key` + checksum) |
| Recomputed often / TTL-friendly | **Redis** |

---

## Project layout

```text
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── core/
│   │   ├── config.py           # pydantic-settings (.env)
│   │   ├── security.py         # JWT, bcrypt
│   │   └── database.py         # async SQLAlchemy engine/session
│   ├── models/
│   │   ├── core.py             # fabs, testers, products, lots, wafers
│   │   ├── users.py            # users, user_preferences, audit_logs
│   │   ├── uploads.py          # upload_jobs, pipeline_steps, ai_log_summaries
│   │   ├── analytics.py        # kpi_snapshots, scan_chain_failures, wafer_defect_uploads, alerts, notifications
│   │   └── recommendations.py  # recommendations, recommendation_feedback
│   ├── schemas/common.py       # Pydantic request/response models
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── uploads.py
│   │   ├── dashboard.py
│   │   ├── actions.py
│   │   └── notifications.py  # + recommendation feedback + export PDF
│   ├── services/
│   │   ├── deps.py             # get_current_user, formatters
│   │   └── dashboard_service.py
│   ├── storage/minio_client.py
│   ├── cache/redis_client.py
│   └── workers/
│       ├── parse_worker.py
│       └── ai_worker.py
├── alembic/versions/001_initial_schema.py
├── scripts/seed.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── prompts-backend.csv         # Backend implementation prompts (Phases 1, 3–9)
├── prompts-database.csv        # Database schema prompts (Phase 2)
└── PRODUCTION_HARDENING.md
```

---

## Database schema

**Migration:** `alembic/versions/001_initial_schema.py`  
**Models:** `app/models/`

### Tables (18 in current migration)

| Group | Tables |
|---|---|
| Dimensions | `fabs`, `testers`, `products`, `lots`, `wafers` |
| Auth | `users`, `user_preferences`, `audit_logs` |
| Uploads | `upload_jobs`, `upload_pipeline_steps`, `ai_log_summaries` |
| Analytics | `kpi_snapshots`, `scan_chain_failures`, `wafer_defect_uploads`, `alerts`, `notifications` |
| Recommendations | `recommendations`, `recommendation_feedback` |

### Enums

- `upload_status`: queued, uploading, parsing, processing, completed, failed
- `upload_kind`: data, log
- `wafer_defect_class`: centre, donut, edge-ring, scratch, near-full, normal, edge-loc, local, random

### Indexes

- `idx_kpi_snapshots_filter` — (module, captured_at DESC)
- `idx_alerts_created`, `idx_alerts_lot`
- `idx_upload_jobs_status`
- `idx_wafer_defect_class`
- `idx_rec_feedback_agent`

> **Note:** The platform spec references a full **39-table** schema. Current migration covers all tables listed in Phase 2 of the implementation prompt. Remaining tables require reconciliation against your canonical schema doc.

Full schema prompt details: [`prompts-database.csv`](./prompts-database.csv)

---

## API endpoints

All routes prefixed with `/api/v1` unless noted.

### Auth (`/auth`)

| Method | Path | Description |
|---|---|---|
| POST | `/login` | Email + password → access + refresh tokens |
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Invalidate session |
| GET | `/me` | Current user profile |

### Users (`/users`)

| Method | Path | Description |
|---|---|---|
| PATCH | `/me/preferences` | Update theme/account/filter JSON |

### Uploads (`/uploads`)

| Method | Path | Description |
|---|---|---|
| POST | `/presign` | Create job + presigned MinIO PUT URL |
| POST | `/{job_id}/complete` | Mark upload done, enqueue parse worker |
| GET | `/{job_id}` | Job status + pipeline steps |
| GET | `/{job_id}/status` | SSE progress stream |
| GET | `/data` | Paginated data upload history |
| GET | `/log` | Paginated log upload history |
| DELETE | `/{job_id}` | Delete job |
| GET | `/{job_id}/download` | 302 → presigned MinIO GET |
| GET | `/{job_id}/ai-summary` | Formatted AI log summary (strings) |

### Dashboard (`/dashboard`)

| Method | Path | Description |
|---|---|---|
| GET | `/executive` | Executive KPI bundle |
| GET | `/scan-chain/{tab}` | Scan chain tab data |
| GET | `/mbist/{tab}` | MBIST tab data |
| GET | `/lbist/{tab}` | LBIST tab data |
| GET | `/wafer-analysis/overview` | Wafer overview |
| GET | `/wafer-analysis/{defect_class}` | Defect class tab |
| GET | `/wafer-analysis/{defect_class}/uploads` | Upload list |
| GET | `/recommendation-analysis/{agent}` | Agent tab data |
| GET | `/cost-intelligence/{tab}` | Cost tab data |
| GET | `/alerts/{tab}` | Alerts tab data |

### Search & filters

| Method | Path | Description |
|---|---|---|
| GET | `/search?q=` | Platform search (cached index) |
| GET | `/filters/options` | Filter dropdown options |

### Actions (STEP 49)

| Method | Path | Description |
|---|---|---|
| POST | `/actions/primary/{page_id}` | Trigger primary navbar action → `{job_id}` |
| POST | `/ai-diagnosis/{module}` | Trigger AI diagnosis → `{job_id}` |
| GET | `/actions/{job_id}/status` | SSE job progress + result |

### Notifications (STEP 50)

| Method | Path | Description |
|---|---|---|
| GET | `/notifications` | List user notifications |
| PATCH | `/notifications/read-all` | Mark all read |
| PATCH | `/notifications/{id}/read` | Mark one read |

### Recommendations & export

| Method | Path | Description |
|---|---|---|
| POST | `/recommendations/{id}/feedback` | RL feedback signal |
| POST | `/export/pdf` | Generate PDF → MinIO → presigned URL |

### Root

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check (no prefix) |

**Missing vs spec:** `GET /dashboard/wafer-analysis/images/{upload_id}/{type}` → 302 presigned URL

---

## Redis cache keys

Prefix: `verilumen:` (from `REDIS_PREFIX`)

| Key pattern | TTL | Content |
|---|---|---|
| `session:{user_id}` | 24h (spec) / 7d (current) | Refresh token metadata |
| `jwt:blacklist:{jti}` | token exp | Revoked access tokens |
| `dash:executive:main:{hash}:p1` | 60s | Executive KPI bundle |
| `dash:{module}:{tab}:{hash}:p{N}` | 60s | Module tab page |
| `dash:wafer-analysis:{class}:{hash}:p1` | 120s | Wafer defect bundle |
| `search:index:v1` | 5m | Full search index JSON |
| `job:{job_id}:status` | 1h | `{status, percent, step}` |
| `job:{job_id}:events` | 1h | Pub/sub channel for SSE |
| `ratelimit:{ip}:{route}` | 1m | Request count |
| `notif:unread:{user_id}` | 30s | Unread count (not wired) |

Helper: `filter_cache_key(module, tab, filters, page)` in `app/cache/redis_client.py`

---

## MinIO object keys

| Bucket | Key pattern |
|---|---|
| `verilumen-raw-uploads` | `{kind}/{yyyy}/{mm}/{upload_job_id}/{filename}` |
| `verilumen-parsed` | `{upload_job_id}/summary.json`, `scan-chains.json` |
| `verilumen-wafer-images` | `{lot_code}/{wafer_code}/{defect_class}/wafer.png`, `overlay.png` |
| `verilumen-exports` | `{user_id}/{yyyy}/{mm}/{export_id}/report.pdf` |
| `verilumen-ai-artifacts` | (reserved, not used yet) |

---

## Docker services

| Service | Port | Role |
|---|---|---|
| `postgres` | 5432 | Primary database |
| `redis` | 6379 | Cache + ARQ queue |
| `minio` | 9000, 9001 | Object storage + console |
| `minio-init` | — | One-shot bucket creation |
| `api` | 8000 | FastAPI (optional in compose) |
| `worker` | — | ARQ background jobs |

---

## Environment variables

See [`.env.example`](./.env.example):

```bash
DATABASE_URL=postgresql+asyncpg://verilumen:verilumen@localhost:5432/verilumen
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
REDIS_URL=redis://localhost:6379/0
REDIS_PREFIX=verilumen:
JWT_SECRET=change-me-in-production
JWT_ACCESS_TTL_MIN=15
JWT_REFRESH_TTL_DAYS=7
```

**Docker note:** When running `api`/`worker` inside compose, override hostnames to `postgres`, `redis`, `minio` instead of `localhost`.

---

## Implementation status & gaps

See [`GAP_REPORT.md`](./GAP_REPORT.md) and [`../BUILD_SEQUENCE.md`](../BUILD_SEQUENCE.md) for the unified stage plan.

| Phase | Status |
|---|---|
| 1 Infra | **COMPLETE** |
| 2 Database | **PARTIAL** (18/39 tables) |
| 3 MinIO | **PARTIAL** (worker I/O wired) |
| 4 Redis | **PARTIAL** (rate limit wired) |
| 5 Auth | **PARTIAL** (GET preferences added) |
| 6 Uploads | **PARTIAL** (stub parser) |
| 7 Dashboard | **PARTIAL** (seed KPIs + facts) |
| 8 Notifications | **COMPLETE** |
| 9 Production | **MISSING** |

---

## Prompt documentation (CSV)

Implementation prompts are stored separately:

| File | Scope |
|---|---|
| [`prompts-database.csv`](./prompts-database.csv) | **Phase 2** — schema, tables, indexes, enums, migrations |
| [`prompts-backend.csv`](./prompts-backend.csv) | **Phases 1, 3–9** — infra, MinIO, Redis, auth, uploads, dashboard, notifications, production |

Frontend integration prompts (STEP 40–53): [`../dashboard/prompts-frontend-integration.csv`](../dashboard/prompts-frontend-integration.csv)

---

## Production checklist

Deferred items tracked in [`PRODUCTION_HARDENING.md`](./PRODUCTION_HARDENING.md):

- [ ] Postgres backups + PITR
- [ ] MinIO versioning + replication
- [ ] Redis AOF persistence policy
- [ ] Secrets in vault (not `.env`)
- [ ] Rate limiting middleware — **done** (see `app/middleware/rate_limit.py`)
- [ ] Row-level security by fab/product
- [ ] ClamAV virus scan on uploads
- [ ] OpenTelemetry → Grafana

---

## Dependencies

```
fastapi, uvicorn[standard], sqlalchemy[asyncio]>=2.0, asyncpg, alembic,
redis>=5.0, arq, minio, python-jose[cryptography], passlib[bcrypt],
pydantic-settings, python-multipart, reportlab, email-validator
```

See [`requirements.txt`](./requirements.txt).
