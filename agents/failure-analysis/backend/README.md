# Backend

FastAPI application for FA-FR-001→010 (ingestion through reporting).

## Docs

See the repository documentation set:

- [System Architecture](../docs/01_SYSTEM_ARCHITECTURE.md)
- [API Specification](../docs/04_API_SPECIFICATION.md)
- [Database Design](../docs/03_DATABASE_DESIGN.md)
- [Deployment Guide](../docs/09_DEPLOYMENT_GUIDE.md)

## Quick run

```powershell
pip install -r backend/requirements.txt
Copy-Item .env.example .env
$env:PYTHONPATH = (Get-Location).Path
python -m alembic upgrade head
python -m uvicorn backend.main:app --reload --port 8000
```

OpenAPI: http://localhost:8000/docs
