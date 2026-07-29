"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
    force=True,
)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import DatabaseError, dispose_engine, init_db, rebind_engine
from backend.settings import DatabaseConfigurationError
from backend import models as _models  # noqa: F401 — register ORM metadata including FA-FR-001 tables
from backend.ingestion.ingestion_api import router as ingestion_router
from analytics.pattern_detection.pattern_api import router as pattern_router
from analytics.failure_rates.failure_rate_api import router as failure_rate_router
from analytics.failure_rates.production_api import router as production_failure_rate_router
from backend.classification.classification_api import router as classification_router
from backend.recurring.recurring_api import router as recurring_router
from backend.recurring.production_api import router as production_recurrence_router
from backend.correlation.correlation_api import router as correlation_router
from backend.die_analysis.die_api import router as die_router
from backend.die_analysis.production_api import router as production_die_router
from backend.wafer_analysis.wafer_api import router as wafer_router
from backend.wafer_analysis.production_api import router as production_wafer_router
from backend.root_cause.root_cause_api import router as root_cause_router
from backend.root_cause.production_api import router as production_fault_prediction_router
from backend.reporting.report_api import router as reporting_router
from evaluation.evaluation_api import router as evaluation_router
from evaluation.workbench_api import router as workbench_router
from backend.auth.auth_api import router as auth_router
from backend.auth import models as _auth_models  # noqa: F401 — register auth tables
from backend.pipeline.consume_api import router as pipeline_router
from backend.pipeline.run_api import router as failure_run_router
from backend.settings import get_settings

logger = logging.getLogger("backend.startup")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("FastAPI startup beginning")
    try:
        rebind_engine()
        await init_db()
    except (DatabaseError, DatabaseConfigurationError) as exc:
        logger.error("Database startup failed: %s", exc)
        raise SystemExit(f"Startup aborted: {exc}") from None

    # Bootstrap default administrator when the user table is empty
    try:
        from backend.database import SessionLocal
        from backend.auth.service import AuthService

        async with SessionLocal() as session:
            await AuthService(session).ensure_bootstrap_admin()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Auth bootstrap skipped: %s", exc)

    try:
        from backend.pipeline.platform_ingest import ensure_storage_dirs

        ensure_storage_dirs()
        logger.info("Storage directories ready")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Storage directory setup skipped: %s", exc)

    logger.info("PostgreSQL Connected")
    logger.info("Database Initialized")
    logger.info("Tables Created")
    logger.info("FastAPI Started Successfully")
    logger.info("Application ready")
    yield
    await dispose_engine()


app = FastAPI(
    title="Failure Analysis API",
    description="FA-FR-001..010 + AI Evaluation/Validation/Training Framework",
    version="2.0.0",
    lifespan=lifespan,
)

_cors = [o.strip() for o in get_settings().cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router)
app.include_router(pattern_router)
app.include_router(failure_rate_router)
app.include_router(production_failure_rate_router)
app.include_router(classification_router)
app.include_router(recurring_router)
app.include_router(production_recurrence_router)
app.include_router(correlation_router)
app.include_router(die_router)
app.include_router(production_die_router)
app.include_router(wafer_router)
app.include_router(production_wafer_router)
app.include_router(root_cause_router)
app.include_router(production_fault_prediction_router)
app.include_router(reporting_router)
app.include_router(evaluation_router)
app.include_router(workbench_router)
app.include_router(auth_router)
app.include_router(pipeline_router)
app.include_router(failure_run_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "failure-analysis-api"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Kubernetes-style readiness probe (DB must be reachable)."""
    from sqlalchemy import text
    from backend.database import SessionLocal

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "service": "failure-analysis-api"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "not_ready", "error": str(exc)}
