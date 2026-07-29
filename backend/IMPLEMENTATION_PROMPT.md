# VERILUMEN — Backend & Database Implementation Prompt

> Paste this file into Cursor inside the `backend/` repo, or copy one `## Phase` section at a time. Before Phase 2, point the agent at current Alembic migrations/models and `docker-compose.yml` to reconcile against the real 39-table schema.

See also: [`GAP_REPORT.md`](./GAP_REPORT.md) · [`prompts-backend.csv`](./prompts-backend.csv) · [`prompts-database.csv`](./prompts-database.csv)

---

You are working inside the VERILUMEN repo — FastAPI backend + Next.js frontend. Postgres, Redis, MinIO via docker-compose.

**Goal:** structured data → PostgreSQL · files → MinIO · cache/sessions/jobs → Redis.

**Before writing code:** read models/migrations, `docker-compose.yml`, routers → produce gap report first.

## Rule of thumb

| Data shape | Store |
|---|---|
| JOINs, filtering, pagination, audit | PostgreSQL |
| File/blob > ~100KB | MinIO (`object_key` + checksum in Postgres) |
| Recomputed / TTL-friendly | Redis |

(Full phase details: Phases 1–9 — see `prompts-backend.csv` and `prompts-database.csv` for machine-readable rows.)
