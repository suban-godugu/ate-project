"""ARQ job: orchestrate Scan Chain agents after parse completes."""

from __future__ import annotations

import logging

from app.core.database import AsyncSessionLocal
from app.orchestration.orchestrator import AgentOrchestrator

log = logging.getLogger("verilumen.orchestrator_worker")


async def orchestrate_agents(ctx, upload_job_id: str, from_stage: str | None = None) -> dict:
    async with AsyncSessionLocal() as db:
        try:
            result = await AgentOrchestrator().start(db, upload_job_id, from_stage=from_stage)
            from app.core.metrics import WORKER_JOBS

            WORKER_JOBS.labels(
                job="orchestrate_agents", status="ok" if result.get("ok") else "failed"
            ).inc()
            return result
        except Exception as exc:  # noqa: BLE001
            log.exception(
                "orchestrate_failed",
                extra={"structured_extra": {"upload_id": upload_job_id}},
            )
            from app.core.metrics import WORKER_JOBS

            WORKER_JOBS.labels(job="orchestrate_agents", status="failed").inc()
            return {"ok": False, "error": str(exc)}
