"""Progress helpers — pipeline stages → Redis SSE."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import publish_job_event, set_job_status
from app.domain.pipeline_stages import STAGE_PERCENT, PipelineStage
from app.models.uploads import UploadJob, UploadStatus
from app.repositories import pipeline_repo as repo

log = logging.getLogger("verilumen.progress")


async def mark_stage(
    db: AsyncSession,
    job: UploadJob,
    stage: str,
    *,
    status: str = "active",
    upload_status: UploadStatus | None = None,
    error: str | None = None,
) -> None:
    job_id = str(job.id)
    if status == "active":
        await repo.set_step_status(db, job.id, stage, "active")
    elif status == "done":
        await repo.set_step_status(db, job.id, stage, "done")
    elif status == "failed":
        await repo.set_step_status(db, job.id, stage, "failed")

    if upload_status is not None:
        job.status = upload_status
    if error:
        job.error_message = error

    percent = STAGE_PERCENT.get(stage, 0)
    if stage == PipelineStage.failed:
        percent = STAGE_PERCENT.get(PipelineStage.failed, 0)
    event = {
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "percent": percent,
        "step": stage,
        "error": error,
        "failed_stage": stage if status == "failed" else None,
    }
    await set_job_status(job_id, event)
    await publish_job_event(job_id, event)
    log.info(
        "pipeline_progress",
        extra={"structured_extra": {"upload_id": job_id, "stage": stage, "status": status, "percent": percent}},
    )


async def fail_stage(db: AsyncSession, job: UploadJob, stage: str, message: str) -> None:
    job.status = UploadStatus.failed
    job.error_message = message
    await mark_stage(db, job, stage, status="failed", upload_status=UploadStatus.failed, error=message)
