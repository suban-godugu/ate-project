import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import cache_delete_pattern, get_redis, prefix_key, publish_job_event, set_job_status
from app.core.config import get_settings
from app.core.database import get_db
from app.models.uploads import AILogSummary, UploadJob, UploadKind, UploadPipelineStep, UploadStatus
from app.models.users import User
from app.schemas.common import (
    AILogSummaryOut,
    CompleteUploadRequest,
    JobCreatedResponse,
    PresignRequest,
    PresignResponse,
    UploadJobOut,
)
from app.services.deps import format_currency, format_duration_ms, format_file_size, get_current_user
from app.services.filters import resolve_metadata_fks
from app.services.upload_audit import audit_upload_event
from app.storage.minio_client import (
    build_raw_upload_key,
    delete_object,
    get_presigned_get_url,
    get_presigned_put_url,
)

from app.domain.pipeline_stages import PIPELINE_STEP_DEFS

router = APIRouter(prefix="/uploads", tags=["uploads"])
settings = get_settings()

PIPELINE_STEPS = PIPELINE_STEP_DEFS


@router.post("/presign", response_model=PresignResponse)
async def presign_upload(
    body: PresignRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    job_id = uuid.uuid4()
    kind = UploadKind.data if body.kind == "data" else UploadKind.log
    object_key = build_raw_upload_key(body.kind, str(job_id), body.file_name, now.year, now.month)
    bucket = settings.minio_bucket_raw

    job = UploadJob(
        id=job_id,
        kind=kind,
        module=body.module,
        status=UploadStatus.queued,
        file_name=body.file_name,
        file_type=body.file_name.rsplit(".", 1)[-1] if "." in body.file_name else None,
        size_bytes=body.size,
        uploaded_by=user.id,
        minio_bucket=bucket,
        minio_object_key=object_key,
    )
    fks = await resolve_metadata_fks(db, body.metadata)
    job.fab_id = fks.get("fab_id")
    job.tester_id = fks.get("tester_id")
    job.product_id = fks.get("product_id")
    job.lot_id = fks.get("lot_id")
    job.wafer_id = fks.get("wafer_id")
    db.add(job)
    for step_key, _ in PIPELINE_STEPS:
        db.add(UploadPipelineStep(job_id=job_id, step_key=step_key, status="pending"))
    await db.flush()

    await audit_upload_event(
        db,
        user_id=user.id,
        action="upload_started",
        job=job,
        user=user,
        message="Upload job created",
    )

    upload_url = get_presigned_put_url(bucket, object_key)
    return PresignResponse(job_id=str(job_id), upload_url=upload_url, object_key=object_key)


@router.post("/{job_id}/complete")
async def complete_upload(
    job_id: str,
    body: CompleteUploadRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UploadJob).where(UploadJob.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = UploadStatus.parsing
    if body.checksum_sha256:
        job.checksum_sha256 = body.checksum_sha256
    await db.flush()
    await set_job_status(job_id, {"status": "parsing", "percent": 10, "step": "validate"})
    await publish_job_event(job_id, {"status": "parsing", "percent": 10, "step": "validate"})
    await audit_upload_event(
        db,
        user_id=user.id,
        action="upload_completed",
        job=job,
        user=user,
        status="parsing",
        message="File received and queued for parsing",
    )
    from app.workers.parse_worker import enqueue_parse_job

    await enqueue_parse_job(job_id)
    return {"ok": True}


@router.get("/data")
async def list_data_uploads(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _list_uploads(db, UploadKind.data, page, user)


@router.get("/log")
async def list_log_uploads(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _list_uploads(db, UploadKind.log, page, user)


@router.get("/{job_id}")
async def get_upload_job(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    result = await db.execute(select(UploadJob).where(UploadJob.id == job_uuid))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    steps_result = await db.execute(select(UploadPipelineStep).where(UploadPipelineStep.job_id == job.id))
    steps = steps_result.scalars().all()
    lookups = await _build_job_lookups(db, [job])
    return {
        "job": _job_to_dict(job, lookups),
        "steps": [
            {
                "id": s.step_key,
                "label": dict(PIPELINE_STEP_DEFS).get(s.step_key, s.step_key.replace("_", " ").title()),
                "status": s.status,
            }
            for s in steps
        ],
    }


@router.get("/{job_id}/status")
async def upload_status_stream(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UploadJob).where(UploadJob.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.uploaded_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this upload job")

    async def event_generator():
        redis = await get_redis()
        pubsub = redis.pubsub()
        channel = prefix_key(f"job:{job_id}:events")
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data']}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/{job_id}")
async def delete_upload(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(UploadJob).where(UploadJob.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        delete_object(job.minio_bucket, job.minio_object_key)
    except Exception:
        pass
    await audit_upload_event(
        db,
        user_id=user.id,
        action="upload_cancelled",
        job=job,
        user=user,
        severity="warning",
        status="cancelled",
        message="Upload job deleted by user",
    )
    await db.delete(job)
    await cache_delete_pattern("dash:*")
    return {"ok": True}


@router.get("/{job_id}/download")
async def download_upload(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(UploadJob).where(UploadJob.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    url = get_presigned_get_url(job.minio_bucket, job.minio_object_key)
    return RedirectResponse(url)


@router.get("/{job_id}/ai-summary", response_model=AILogSummaryOut)
async def get_ai_summary(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(AILogSummary).where(AILogSummary.upload_job_id == uuid.UUID(job_id)))
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return AILogSummaryOut(
        filesProcessed=str(summary.files_processed or 0),
        patternsFound=str(summary.patterns_found or 0),
        scanChains=str(summary.scan_chains or 0),
        memoryBlocks=str(summary.memory_blocks or 0),
        logicBlocks=str(summary.logic_blocks or 0),
        waferCount=str(summary.wafer_count or 0),
        defectsFound=str(summary.defects_found or 0),
        yield_=f"{summary.yield_pct or 0}%",
        estimatedTestCost=format_currency(float(summary.estimated_cost or 0)),
        estimatedSavings=format_currency(float(summary.estimated_savings or 0)),
    )


async def _list_uploads(db: AsyncSession, kind: UploadKind, page: int, user: User) -> dict:
    offset = (page - 1) * 20
    result = await db.execute(
        select(UploadJob)
        .where(UploadJob.kind == kind)
        .order_by(UploadJob.created_at.desc())
        .offset(offset)
        .limit(20)
    )
    jobs = result.scalars().all()
    lookups = await _build_job_lookups(db, jobs)
    return {"items": [_job_to_dict(j, lookups) for j in jobs], "page": page}


async def _build_job_lookups(db: AsyncSession, jobs: list[UploadJob]) -> dict:
    from app.models.core import Lot, Tester, Wafer

    user_ids = {j.uploaded_by for j in jobs if j.uploaded_by}
    lot_ids = {j.lot_id for j in jobs if j.lot_id}
    wafer_ids = {j.wafer_id for j in jobs if j.wafer_id}
    tester_ids = {j.tester_id for j in jobs if j.tester_id}

    users = {}
    if user_ids:
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: u.name for u in result.scalars().all()}

    lots = {}
    if lot_ids:
        result = await db.execute(select(Lot).where(Lot.id.in_(lot_ids)))
        lots = {l.id: l.lot_code for l in result.scalars().all()}

    wafers = {}
    if wafer_ids:
        result = await db.execute(select(Wafer).where(Wafer.id.in_(wafer_ids)))
        wafers = {w.id: w.wafer_code for w in result.scalars().all()}

    testers = {}
    if tester_ids:
        result = await db.execute(select(Tester).where(Tester.id.in_(tester_ids)))
        testers = {t.id: t.name for t in result.scalars().all()}

    return {"users": users, "lots": lots, "wafers": wafers, "testers": testers}


def _job_to_dict(job: UploadJob, lookups: dict | None = None) -> dict:
    lookups = lookups or {}
    users = lookups.get("users", {})
    lots = lookups.get("lots", {})
    wafers = lookups.get("wafers", {})
    testers = lookups.get("testers", {})
    status_map = {
        UploadStatus.queued: "Queued",
        UploadStatus.uploading: "Uploading",
        UploadStatus.parsing: "Parsing",
        UploadStatus.processing: "Processing",
        UploadStatus.completed: "Completed",
        UploadStatus.failed: "Failed",
    }
    return {
        "id": str(job.id),
        "fileName": job.file_name,
        "module": job.module,
        "fileType": job.file_type or "",
        "size": format_file_size(job.size_bytes),
        "uploadedBy": users.get(job.uploaded_by, "Unknown"),
        "uploadTime": job.created_at.isoformat() if job.created_at else "",
        "status": status_map.get(job.status, "Queued"),
        "processingTime": format_duration_ms(job.processing_ms),
        "tester": testers.get(job.tester_id, ""),
        "lotId": lots.get(job.lot_id, ""),
        "waferId": wafers.get(job.wafer_id, ""),
    }
