# VERILUMEN End-to-End Share Package

Portable layout of the full ATE Intelligence / VERILUMEN stack.

**Full architecture (how frontend, backend, DB, and agents connect, tech stacks, run commands):** see **[README.md](./README.md)**.

| Folder | Role |
|--------|------|
| `dashboard/` | Next.js main UI (`:3000`) |
| `backend/` | FastAPI platform API + ARQ worker (`:8000`) |
| `agents/pattern-analysis/` | Pattern Analysis agent (`:8011`) |
| `agents/failure-analysis/` | Failure Analysis API (`:8021`) + UI (`:3020`) |
| `agents/scan-diagnosis/` | Scan Diagnosis API (`:8031`) + UI (`:3030`) |
| `agents/pattern-recommendation/` | Pattern Recommendation (`:8041` / `:3041`) |
| `agents/scan-debug-recommendation/` | Scan Debug Recommendation (`:8042` / `:3042`) |
| `agents/test-optimization/` | Test Optimization (`:8043` / `:3043`) |
| `agents/spatial-ai/` | Spatial / WaferVision (optional) |
| `runtime/` | Local input / output / MinIO data / logs |

## Prerequisites (Windows)

1. **Python 3.11+** on PATH
2. **Node.js 20+** and npm on PATH
3. **PostgreSQL** listening on `127.0.0.1:5432`
4. **Redis** (`redis-server`) and **MinIO** (`minio`) on PATH
5. Create DBs / users as described in each project's `.env.example`

## First-time setup

```powershell
# 1. Unzip anywhere, then open PowerShell in this folder

# 2. Backend Python deps
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # edit DATABASE_URL, Redis, MinIO, JWT secrets
# run migrations if the project uses Alembic:
# alembic upgrade head
cd ..

# 3. Dashboard
cd dashboard
copy .env.example .env.local   # or create .env.local from docs
npm install
cd ..

# 4. Each agent UI that has package.json
#    (failure-analysis\ate-dashboard, scan-diagnosis\frontend,
#     pattern-recommendation\frontend, scan-debug-recommendation\frontend,
#     test-optimization\frontend)
#    Run: npm install
#    And for each Python agent: pip install -r requirements.txt (in venv or global)
```

## Run everything

```powershell
powershell -ExecutionPolicy Bypass -File .\start-stack.ps1
```

Open: **http://localhost:3000/dashboard**

Stop:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop-stack.ps1
```

## Notes

- Runtime uploads/models/output data are **not** included (package stays shareable size).
- Put sample inputs under `runtime\input\` after unzip.
- Agent UI ports are **proxied through the dashboard** — use the dashboard, not the raw agent ports.
- Change default secrets (`dev-service-key-change-me`, MinIO password, JWT) before any shared/demo environment.
