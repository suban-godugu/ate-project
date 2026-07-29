# Failure Analysis Agent

AI-powered semiconductor failure analysis platform for STIL files and tester logs. Production pipeline covers **FA-FR-001 → FA-FR-010** (ingest → patterns → rates → classification → recurrence → correlation → die → wafer → fault prediction → reports).

## Documentation

| # | Document | Description |
|---|----------|-------------|
| 01 | [System Architecture](docs/01_SYSTEM_ARCHITECTURE.md) | Modules, stack, lineage, logging & observability |
| 02 | [Software Design Specification](docs/02_SOFTWARE_DESIGN_SPECIFICATION.md) | Layers, patterns, services, queues, events |
| 03 | [Database Design](docs/03_DATABASE_DESIGN.md) | PostgreSQL schema, migrations, indexes |
| 04 | [API Specification](docs/04_API_SPECIFICATION.md) | Endpoints, DTOs, error codes |
| 05 | [AI Architecture](docs/05_AI_ARCHITECTURE.md) | Prediction, confidence, prompts, evaluation, RAG |
| 06 | [Parser Framework](docs/06_PARSER_FRAMEWORK.md) | Parser factory, adapters, validation, plugins |
| 07 | [Security Architecture](docs/07_SECURITY_ARCHITECTURE.md) | AuthN/Z, secrets, OWASP, upload security |
| 08 | [Performance and Testing](docs/08_PERFORMANCE_AND_TESTING.md) | SLAs, scalability, benchmarks, tests |
| 09 | [Deployment Guide](docs/09_DEPLOYMENT_GUIDE.md) | Local/prod run, Docker/K8s, backup & DR |
| 10 | [User Guide](docs/10_USER_GUIDE.md) | Dashboard workflow and operator help |

## Quick start

```powershell
# One-shot (API :8000 + dashboard :3000) from repo root
Copy-Item .env.example .env   # set DATABASE_PASSWORD
pip install -r backend/requirements.txt
python -m alembic upgrade head
.\start-dashboard.ps1
```

Or manually:

```powershell
# API
$env:PYTHONPATH = (Get-Location).Path
python -m uvicorn backend.main:app --reload --port 8000

# Production dashboard (run from ate-dashboard so Turbopack root is correct)
cd ate-dashboard
npm install
npm run dev
```

- API: http://localhost:8000/docs  
- Dashboard: http://127.0.0.1:3000/overview  

If all routes 404 but the sidebar still shows, Turbopack root was wrong — ensure `ate-dashboard/next.config.ts` pins `turbopack.root` to the `ate-dashboard` directory (caused by a parent `package-lock.json`). See [ate-dashboard/README.md](ate-dashboard/README.md).

Details: [Deployment Guide](docs/09_DEPLOYMENT_GUIDE.md) · [User Guide](docs/10_USER_GUIDE.md).

## Functional modules

| ID | Capability |
|----|------------|
| FA-FR-001 | Test data ingestion |
| FA-FR-002 | Failure pattern detection |
| FA-FR-003 | Failure rate computation |
| FA-FR-004 | Fault classification |
| FA-FR-005 | Recurring failure identification |
| FA-FR-006 | Failure-to-pattern correlation |
| FA-FR-007 | Die-level analysis |
| FA-FR-008 | Wafer-level analysis |
| FA-FR-009 | AI-based fault type prediction |
| FA-FR-010 | Enterprise reporting |

## CLI (optional)

```powershell
python main.py --log-dir tests/fixtures --use-adapter-ingestion --recursive
python dashboard.py
```

## Prompt logging

Cursor prompts are recorded for this workspace (`prompt_log.csv`, `PROMPT_LOG.md`, `prompt_archive/`). See `.cursor/hooks.json`.

## Requirements

- Python 3.12+ (API); Node.js 20+ (`ate-dashboard`)
- PostgreSQL (required for production API)
- Optional: Redis, MinIO, ML extras (`requirements-ml.txt`)
