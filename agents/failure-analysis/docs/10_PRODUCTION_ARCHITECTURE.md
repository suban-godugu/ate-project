# Production Readiness — Architecture

## Overview

The Verilumen Semiconductor Failure Analysis stack has three layers:

1. **ate-dashboard** (Next.js) — enterprise glassmorphism UI, Zustand + TanStack Query
2. **backend** (FastAPI) — FA-FR-001→010 pipeline, auth, audit, system health
3. **PostgreSQL + Redis** — persistence and optional Celery broker

```
Browser → NGINX → Dashboard (:3000) ──/api/*──→ FastAPI (:8000) → PostgreSQL
                                      ↑ JWT Bearer + X-User-Id / X-Role
```

## Authentication

- `POST /api/v1/auth/login` — email/password → access + refresh tokens
- `POST /api/v1/auth/refresh` — rotate refresh, issue new access
- `POST /api/v1/auth/logout` — revoke refresh token
- `GET /api/v1/auth/me` — current user

Access tokens are short-lived JWTs (HS256). Refresh tokens are opaque, hashed at rest, and rotated on use.

## RBAC

| Role | Capabilities |
|------|----------------|
| Administrator | Users, settings, audit, all engineer capabilities |
| Engineer | Upload, run analysis, reports, storage |
| Operator | Dashboard, monitor analysis, system health |
| Viewer | Read-only overview |

Frontend: `src/lib/rbac.ts` + Sidebar filtering + AuthGuard.
Backend: `backend/auth/security.py` dependencies (`AdminUser`, `EngineerUser`, …).

## Folder structure (auth & ops)

```
backend/auth/
  models.py       users, refresh tokens, settings, notifications, audit
  security.py     JWT, passwords, RBAC deps
  repository.py   persistence
  service.py      login/refresh/bootstrap
  auth_api.py     HTTP routes

ate-dashboard/src/
  app/login|users|settings|audit|system-health|storage/
  components/AuthGuard|AppShell|TopBar|NotificationCenter|Sidebar
  stores/authStore|settingsStore|notificationStore
  lib/config|logger|rbac|http
  services/auth.ts
  middleware.ts
```

## Observability

- `GET /health` — liveness
- `GET /ready` — readiness (DB ping)
- `GET /api/v1/system/health` — CPU/memory/disk/API latency/storage
- Frontend logger: `src/lib/logger.ts` (route changes, API errors, analysis events)
