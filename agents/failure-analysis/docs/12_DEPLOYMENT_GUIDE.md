# Deployment Guide

## Prerequisites

- Docker + Docker Compose
- Strong `JWT_SECRET` and `DATABASE_PASSWORD`
- `AUTH_REQUIRED=true` and `NEXT_PUBLIC_AUTH_ENABLED=true` in production

## Quick start

```bash
cp .env.example .env
# edit DATABASE_PASSWORD, JWT_SECRET, BOOTSTRAP_ADMIN_PASSWORD

docker compose up --build -d
```

Services:

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80 | Reverse proxy |
| dashboard | 3000 | Next.js UI |
| api | 8000 | FastAPI |
| db | 5432 | PostgreSQL |
| redis | 6379 | Broker / cache |

Health checks:

- `GET http://localhost/health` — API liveness
- `GET http://localhost/ready` — API readiness (DB)
- Compose healthchecks on `api`, `db`, and dashboard containers

## Local development (without Docker)

```bash
# API
uvicorn backend.main:app --reload --port 8000

# Dashboard
cd ate-dashboard
cp .env.example .env.local
npm run dev
```

With `NEXT_PUBLIC_AUTH_ENABLED=false` and `AUTH_REQUIRED=false`, the UI works without login (dev only).

## Production checklist

1. Set unique `JWT_SECRET` (≥32 chars)
2. Change bootstrap admin password after first login
3. Restrict `CORS_ORIGINS`
4. Enable `AUTH_REQUIRED=true`
5. Terminate TLS at NGINX or a load balancer
6. Persist `pgdata` volume backups
7. Monitor `/api/v1/system/health`

## Environment validation

Backend settings fail fast when `DATABASE_PASSWORD` is missing or still `CHANGE_ME`.
JWT and auth flags are loaded via `backend/settings.py` (`JWT_SECRET`, `AUTH_REQUIRED`, …).
