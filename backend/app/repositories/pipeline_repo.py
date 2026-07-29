"""Repository helpers for Scan Chain pipeline tables."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import (
    AgentExecutionLog,
    DashboardMetric,
    DiagnosisResult,
    FailureResult,
    NormalizedRecord,
    ParsedFile,
    ParserJob,
    ParserJobStatus,
    ParserStatistics,
    PatternResult,
    RecommendationResult,
)
from app.models.uploads import UploadJob, UploadPipelineStep


async def get_upload_job(db: AsyncSession, upload_id: uuid.UUID) -> UploadJob | None:
    return await db.get(UploadJob, upload_id)


async def find_duplicate_by_sha256(db: AsyncSession, sha256: str, exclude_upload_id: uuid.UUID) -> ParserJob | None:
    result = await db.execute(
        select(ParserJob)
        .where(
            ParserJob.sha256 == sha256,
            ParserJob.status == ParserJobStatus.completed,
            ParserJob.upload_job_id != exclude_upload_id,
        )
        .order_by(ParserJob.completed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_parser_job(db: AsyncSession, upload_job_id: uuid.UUID, **kwargs: Any) -> ParserJob:
    job = ParserJob(id=uuid.uuid4(), upload_job_id=upload_job_id, **kwargs)
    db.add(job)
    await db.flush()
    return job


async def save_statistics(db: AsyncSession, parser_job_id: uuid.UUID, **kwargs: Any) -> ParserStatistics:
    stats = ParserStatistics(id=uuid.uuid4(), parser_job_id=parser_job_id, **kwargs)
    db.add(stats)
    await db.flush()
    return stats


async def create_parsed_file(db: AsyncSession, **kwargs: Any) -> ParsedFile:
    row = ParsedFile(id=uuid.uuid4(), **kwargs)
    db.add(row)
    await db.flush()
    return row


async def bulk_insert_normalized(
    db: AsyncSession,
    upload_job_id: uuid.UUID,
    parser_job_id: uuid.UUID,
    records: Sequence[dict[str, Any]],
    parsed_file_id: uuid.UUID | None = None,
) -> int:
    for payload in records:
        db.add(
            NormalizedRecord(
                id=uuid.uuid4(),
                upload_job_id=upload_job_id,
                parser_job_id=parser_job_id,
                parsed_file_id=parsed_file_id,
                lot_id=payload.get("lot_id") or None,
                wafer_id=payload.get("wafer_id") or None,
                die_id=payload.get("die_id") or None,
                pass_fail=payload.get("pass_fail") or None,
                scan_chain=payload.get("scan_chain") or None,
                payload=payload,
            )
        )
    await db.flush()
    return len(records)


async def list_normalized_payloads(db: AsyncSession, upload_job_id: uuid.UUID) -> list[dict[str, Any]]:
    result = await db.execute(
        select(NormalizedRecord.payload).where(NormalizedRecord.upload_job_id == upload_job_id)
    )
    return [row[0] for row in result.all()]


async def upsert_pattern_result(db: AsyncSession, upload_job_id: uuid.UUID, **kwargs: Any) -> PatternResult:
    existing = await db.scalar(select(PatternResult).where(PatternResult.upload_job_id == upload_job_id))
    if existing:
        for k, v in kwargs.items():
            setattr(existing, k, v)
        await db.flush()
        return existing
    row = PatternResult(id=uuid.uuid4(), upload_job_id=upload_job_id, **kwargs)
    db.add(row)
    await db.flush()
    return row


async def upsert_failure_result(db: AsyncSession, upload_job_id: uuid.UUID, **kwargs: Any) -> FailureResult:
    existing = await db.scalar(select(FailureResult).where(FailureResult.upload_job_id == upload_job_id))
    if existing:
        for k, v in kwargs.items():
            setattr(existing, k, v)
        await db.flush()
        return existing
    row = FailureResult(id=uuid.uuid4(), upload_job_id=upload_job_id, **kwargs)
    db.add(row)
    await db.flush()
    return row


async def upsert_diagnosis_result(db: AsyncSession, upload_job_id: uuid.UUID, **kwargs: Any) -> DiagnosisResult:
    existing = await db.scalar(select(DiagnosisResult).where(DiagnosisResult.upload_job_id == upload_job_id))
    if existing:
        for k, v in kwargs.items():
            setattr(existing, k, v)
        await db.flush()
        return existing
    row = DiagnosisResult(id=uuid.uuid4(), upload_job_id=upload_job_id, **kwargs)
    db.add(row)
    await db.flush()
    return row


async def upsert_recommendation_result(
    db: AsyncSession, upload_job_id: uuid.UUID, **kwargs: Any
) -> RecommendationResult:
    existing = await db.scalar(
        select(RecommendationResult).where(RecommendationResult.upload_job_id == upload_job_id)
    )
    if existing:
        for k, v in kwargs.items():
            setattr(existing, k, v)
        await db.flush()
        return existing
    row = RecommendationResult(id=uuid.uuid4(), upload_job_id=upload_job_id, **kwargs)
    db.add(row)
    await db.flush()
    return row


async def upsert_dashboard_metrics(db: AsyncSession, upload_job_id: uuid.UUID, **kwargs: Any) -> DashboardMetric:
    existing = await db.scalar(select(DashboardMetric).where(DashboardMetric.upload_job_id == upload_job_id))
    if existing:
        for k, v in kwargs.items():
            setattr(existing, k, v)
        existing.updated_at = datetime.now(UTC)
        await db.flush()
        return existing
    row = DashboardMetric(id=uuid.uuid4(), upload_job_id=upload_job_id, **kwargs)
    db.add(row)
    await db.flush()
    return row


async def log_execution(
    db: AsyncSession,
    upload_job_id: uuid.UUID,
    *,
    stage: str,
    status: str,
    agent: str | None = None,
    attempt: int = 1,
    latency_ms: float | None = None,
    error_message: str | None = None,
    extras: dict | None = None,
) -> AgentExecutionLog:
    row = AgentExecutionLog(
        id=uuid.uuid4(),
        upload_job_id=upload_job_id,
        stage=stage,
        agent=agent,
        attempt=attempt,
        status=status,
        latency_ms=latency_ms,
        error_message=error_message,
        extras=extras,
    )
    db.add(row)
    await db.flush()
    return row


async def get_pipeline_steps(db: AsyncSession, job_id: uuid.UUID) -> list[UploadPipelineStep]:
    result = await db.execute(select(UploadPipelineStep).where(UploadPipelineStep.job_id == job_id))
    return list(result.scalars().all())


async def set_step_status(
    db: AsyncSession, job_id: uuid.UUID, step_key: str, status: str
) -> UploadPipelineStep | None:
    result = await db.execute(
        select(UploadPipelineStep).where(
            UploadPipelineStep.job_id == job_id, UploadPipelineStep.step_key == step_key
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        return None
    step.status = status
    if status == "active":
        step.started_at = datetime.now(UTC)
    elif status in ("done", "failed"):
        step.finished_at = datetime.now(UTC)
    await db.flush()
    return step


async def get_aggregated_results(db: AsyncSession, upload_job_id: uuid.UUID) -> dict[str, Any]:
    pattern = await db.scalar(select(PatternResult).where(PatternResult.upload_job_id == upload_job_id))
    failure = await db.scalar(select(FailureResult).where(FailureResult.upload_job_id == upload_job_id))
    diagnosis = await db.scalar(select(DiagnosisResult).where(DiagnosisResult.upload_job_id == upload_job_id))
    rec = await db.scalar(select(RecommendationResult).where(RecommendationResult.upload_job_id == upload_job_id))
    metrics = await db.scalar(select(DashboardMetric).where(DashboardMetric.upload_job_id == upload_job_id))
    parser = await db.scalar(
        select(ParserJob).where(ParserJob.upload_job_id == upload_job_id).order_by(ParserJob.created_at.desc())
    )
    return {
        "upload_id": str(upload_job_id),
        "parser_job": {
            "id": str(parser.id) if parser else None,
            "status": parser.status.value if parser else None,
            "parser_id": parser.parser_id if parser else None,
            "unified_dataset_key": parser.unified_dataset_key if parser else None,
            "failed_stage": parser.failed_stage if parser else None,
        },
        "pattern": {
            "status": pattern.status if pattern else None,
            "report": pattern.report if pattern else None,
            "kpis": pattern.kpis if pattern else None,
            "artifact_key": pattern.artifact_key if pattern else None,
            "error": pattern.error_message if pattern else None,
        },
        "failure": {
            "status": failure.status if failure else None,
            "report": failure.report if failure else None,
            "yield_report": failure.yield_report if failure else None,
            "kpis": failure.kpis if failure else None,
            "artifact_key": failure.artifact_key if failure else None,
            "error": failure.error_message if failure else None,
        },
        "diagnosis": {
            "status": diagnosis.status if diagnosis else None,
            "report": diagnosis.report if diagnosis else None,
            "kpis": diagnosis.kpis if diagnosis else None,
            "recommendations": diagnosis.recommendations if diagnosis else None,
            "confidence": diagnosis.confidence if diagnosis else None,
            "artifact_key": diagnosis.artifact_key if diagnosis else None,
            "error": diagnosis.error_message if diagnosis else None,
        },
        "recommendations": {
            "status": rec.status if rec else None,
            "payload": rec.payload if rec else None,
            "kpis": rec.kpis if rec else None,
        },
        "dashboard_metrics": {
            "executive_kpis": metrics.executive_kpis if metrics else None,
            "pattern_kpis": metrics.pattern_kpis if metrics else None,
            "failure_kpis": metrics.failure_kpis if metrics else None,
            "diagnosis_kpis": metrics.diagnosis_kpis if metrics else None,
            "recommendation_kpis": metrics.recommendation_kpis if metrics else None,
        },
    }
