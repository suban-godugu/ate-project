"""Jobs / progress / results / retry APIs for Scan Chain pipeline."""

from __future__ import annotations

import uuid
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_job_status
from app.core.config import get_settings
from app.core.database import get_db
from app.domain.pipeline_stages import PIPELINE_STEP_DEFS, STAGE_PERCENT
from app.models.uploads import UploadJob
from app.models.users import User
from app.repositories import pipeline_repo as repo
from app.services.deps import get_current_user
from app.workers.parse_worker import enqueue_parse_job

router = APIRouter(tags=["jobs"])
settings = get_settings()


class RetryBody(BaseModel):
    stage: str | None = None


class OrchestratorStartBody(BaseModel):
    upload_id: str
    from_stage: str | None = Field(default=None)


def _job_out(job: UploadJob, steps: list[Any] | None = None, status: dict | None = None) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "file_name": job.file_name,
        "module": job.module,
        "kind": job.kind.value if hasattr(job.kind, "value") else str(job.kind),
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "error_message": job.error_message,
        "checksum_sha256": job.checksum_sha256,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "steps": [
            {
                "id": s.step_key,
                "label": dict(PIPELINE_STEP_DEFS).get(s.step_key, s.step_key),
                "status": s.status,
            }
            for s in (steps or [])
        ],
        "progress": status,
    }


@router.get("/jobs")
async def list_jobs(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UploadJob).where(UploadJob.uploaded_by == user.id).order_by(UploadJob.created_at.desc()).limit(limit)
    )
    jobs = list(result.scalars().all())
    return [_job_out(j) for j in jobs]


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(UploadJob, uuid.UUID(job_id))
    if job is None or job.uploaded_by != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    steps = await repo.get_pipeline_steps(db, job.id)
    status = await get_job_status(job_id)
    return _job_out(job, steps, status)


@router.get("/progress/{job_id}")
async def get_progress(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(UploadJob, uuid.UUID(job_id))
    if job is None or job.uploaded_by != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    status = await get_job_status(job_id) or {}
    step = status.get("step")
    return {
        "upload_id": job_id,
        "status": job.status.value,
        "step": step,
        "percent": status.get("percent") or STAGE_PERCENT.get(step or "", 0),
        "error": job.error_message or status.get("error"),
        "failed_stage": status.get("failed_stage"),
        "labels": dict(PIPELINE_STEP_DEFS),
    }


@router.get("/results/{job_id}")
async def get_results(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(UploadJob, uuid.UUID(job_id))
    if job is None or job.uploaded_by != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return await repo.get_aggregated_results(db, job.id)


@router.post("/retry/{job_id}")
async def retry_job(
    job_id: str,
    body: RetryBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(UploadJob, uuid.UUID(job_id))
    if job is None or job.uploaded_by != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    stage = body.stage
    # Re-parse if failure was in parse stages
    parse_stages = {
        "validating",
        "detecting_format",
        "parsing",
        "generating_metadata",
        "normalizing",
    }
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    if stage in parse_stages or (not stage and job.error_message and "Parser" in (job.error_message or "")):
        await enqueue_parse_job(job_id)
        return {"ok": True, "action": "reparse", "upload_id": job_id}
    await redis.enqueue_job("orchestrate_agents", job_id, stage)
    return {"ok": True, "action": "reorchestrate", "upload_id": job_id, "from_stage": stage}


@router.post("/orchestrator/start")
async def orchestrator_start(
    body: OrchestratorStartBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(UploadJob, uuid.UUID(body.upload_id))
    if job is None or job.uploaded_by != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    await redis.enqueue_job("orchestrate_agents", body.upload_id, body.from_stage)
    return {"ok": True, "upload_id": body.upload_id, "from_stage": body.from_stage}
