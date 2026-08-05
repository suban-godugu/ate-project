"""ARQ parse worker — delegates to ParserPipelineService (Parser Engine v2 only)."""

from __future__ import annotations

import logging
import uuid

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.uploads import UploadJob
from app.services.parser_pipeline import ParserPipelineService

log = logging.getLogger("verilumen.parse_worker")
settings = get_settings()


async def enqueue_parse_job(job_id: str) -> None:
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("parse_upload", job_id)


async def parse_upload(ctx, job_id: str) -> dict:
    """Download from MinIO → ParserEngineV2 → unified dataset → enqueue orchestrate_agents."""
    # Free-tier death loop: OOM kill → restart → retry same huge STIL forever.
    tries = int(ctx.get("job_try") or 1)
    if tries >= 2 and settings.parser_light_mode:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(UploadJob).where(UploadJob.id == uuid.UUID(job_id)))
            job = result.scalar_one_or_none()
            if job is not None:
                from app.models.uploads import UploadStatus
                from app.orchestration.progress import fail_stage
                from app.domain.pipeline_stages import PipelineStage

                msg = (
                    "Parse aborted after retry (free-tier memory limit). "
                    "Use a smaller STIL/log, or upgrade ate-api to 2GB and set ENABLE_INLINE_WORKER=1."
                )
                await fail_stage(db, job, PipelineStage.parsing, msg)
                await db.commit()
            return {"ok": False, "error": "aborted_oom_retry", "try": tries}

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UploadJob).where(UploadJob.id == uuid.UUID(job_id)))
        job = result.scalar_one_or_none()
        if job is None:
            log.error("upload_job_missing", extra={"structured_extra": {"upload_id": job_id}})
            return {"error": "job_not_found"}
        try:
            outcome = await ParserPipelineService().run(db, job)
            from app.core.metrics import WORKER_JOBS

            WORKER_JOBS.labels(job="parse_upload", status="ok" if outcome.get("ok") else "failed").inc()
            return outcome
        except Exception as exc:  # noqa: BLE001
            log.exception("parse_upload_failed", extra={"structured_extra": {"upload_id": job_id}})
            job.error_message = str(exc)
            from app.models.uploads import UploadStatus
            from app.orchestration.progress import fail_stage
            from app.domain.pipeline_stages import PipelineStage

            await fail_stage(db, job, PipelineStage.parsing, str(exc))
            await db.commit()
            from app.core.metrics import WORKER_JOBS

            WORKER_JOBS.labels(job="parse_upload", status="failed").inc()
            return {"error": str(exc)}
