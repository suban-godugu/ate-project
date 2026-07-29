# VERILUMEN — Production Hardening (Tier 1 & 2)

**Last updated:** 2026-07-06  
**Scope:** Single-tenant enterprise deployment readiness. Tier 3 (OpenTelemetry, Grafana, ClamAV, Vault, K8s, RLS) is deferred.

---

## Tier 1 — Operational visibility

| Item | Status | Location |
|------|--------|----------|
| Structured JSON logging | Done | `app/core/logging_config.py` |
| Request ID middleware (`X-Request-ID`) | Done | `app/middleware/request_id.py` |
| Request logging + duration | Done | `app/middleware/logging_middleware.py` |
| Audit log correlation | Done | `request_id` in `write_audit_log` meta |
| Upload / parser lifecycle audit | Done | `upload_audit.py`, `uploads.py`, `parse_worker.py` |
| Theme preference sync (`theme_json`) | Done | `GET/PATCH /users/me/preferences`, dashboard `useThemePreferencesSync` |
| `GET /audit` (paginated, role-filtered) | Done | `app/routers/audit.py`, `app/services/audit_query.py` |
| `GET /health` (DB, Redis, MinIO, worker) | Done | `app/routers/operations.py` |
| `GET /ready` (503 if deps down) | Done | `app/routers/operations.py` |
| `GET /live` (liveness, no deps) | Done | `app/routers/operations.py` |
| `GET /metrics` (Prometheus) | Done | `app/routers/operations.py`, `app/core/metrics.py` |
| Consistent JSON error responses | Done | `app/core/exception_handlers.py` |
| Worker heartbeat | Done | `app/workers/heartbeat.py`, ARQ `on_startup` |

### Prometheus metrics exposed

- `verilumen_http_requests_total`, `verilumen_http_request_duration_seconds`
- `verilumen_uploads_total`, `verilumen_upload_duration_seconds`, `verilumen_parser_duration_seconds`
- `verilumen_failed_uploads_total`, `verilumen_worker_jobs_total`
- `verilumen_cache_hits_total`, `verilumen_cache_misses_total`
- `verilumen_recommendations_total`, `verilumen_alerts_total` (gauges)

---

## Tier 2 — Backups, secrets, security

| Item | Status | Location |
|------|--------|----------|
| Postgres backup script | Done | `scripts/backup_db.py` |
| Postgres restore script | Done | `scripts/restore_db.py` |
| Backup retention (daily/weekly/monthly) | Done | `scripts/backup_db.py` |
| Config validation at startup | Done | `app/core/startup_validation.py` |
| Secrets via environment variables | Done | `.env.example` (never commit `.env`) |
| Security response headers | Done | `app/middleware/security_headers.py` |
| CORS restricted methods/headers | Done | `app/main.py` |
| Rate limiting (existing) | Done | `app/middleware/rate_limit.py` |
| Redis policy documented | Done | below |
| MinIO bucket init + healthcheck | Done | `docker-compose.yml`, `minio-init` |
| Docker healthchecks (API, worker) | Done | `docker-compose.yml` |
| CI pipeline | Done | `.github/workflows/ci.yml` |

### Redis policy

**Current choice: AOF persistence enabled** (`redis-server --appendonly yes` in `docker-compose.yml`).

Redis stores:

- JWT session metadata and blacklist
- Dashboard cache keys
- Job status and pub/sub
- Rate limit counters
- Worker heartbeat

Sessions and job state benefit from AOF. Pure-cache mode (no persistence) is acceptable only if you accept session loss on Redis restart — not recommended for this platform.

### MinIO (Tier 2 only)

- Buckets created by `minio-init` service
- Healthcheck on `/minio/health/live`
- **Not implemented (Tier 3):** versioning, replication

### Backup usage

```bash
# Create backup
cd backend
python scripts/backup_db.py --output-dir backups

# Restore (destructive — overwrites schema/data from dump)
python scripts/restore_db.py backups/verilumen_YYYYMMDDTHHMMSSZ.sql.gz
```

Schedule daily backups via cron or your orchestrator. For PITR, configure Postgres WAL archiving separately (Tier 3 / DBA task).

---

## Architecture — monitoring

```
Client → X-Request-ID → FastAPI → Prometheus /metrics
                      ↘ structured JSON logs
                      ↘ audit_logs.meta.request_id

Probe endpoints:
  /live   → process alive (K8s liveness)
  /ready  → DB + Redis + MinIO + worker (K8s readiness)
  /health → full status JSON (ops dashboard)
  /metrics → Prometheus scrape target
```

---

## Deployment checklist

1. Set `ENVIRONMENT=production`
2. Rotate `JWT_SECRET`, `MINIO_SECRET_KEY`, Postgres password
3. Set `CORS_ORIGINS` to your dashboard origin(s) only
4. Enable `ENABLE_HSTS=true` when serving HTTPS
5. Run `alembic upgrade head` and seed
6. Start API + ARQ worker
7. Verify `GET /ready` returns 200
8. Schedule `scripts/backup_db.py`
9. Point Prometheus at `http://api:8000/metrics`

---

## Deferred — Tier 3 (future prompt)

- [ ] OpenTelemetry + Grafana + Tempo/Jaeger
- [ ] Promtail / centralized log aggregation
- [ ] ClamAV upload scanning
- [ ] HashiCorp Vault / external secrets manager
- [ ] MinIO versioning and replication
- [ ] Postgres PITR / WAL archiving automation
- [ ] Row-level security (multi-tenant)
- [ ] Kubernetes manifests / Helm
