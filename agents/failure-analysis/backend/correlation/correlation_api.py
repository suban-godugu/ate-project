"""Production REST API for FA-FR-006 failure-to-pattern correlation."""

from __future__ import annotations

from typing import Any

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.correlation.correlation_repository import CorrelationRepository
from backend.correlation.correlation_service import CorrelationService
from backend.correlation.production_engine import CorrelationComputationError, CorrelationConfig
from backend.correlation.production_repository import ProductionCorrelationRepository
from backend.correlation.production_service import (
    CorrelationValidationError,
    ProductionCorrelationService,
    serialize_correlation,
)
from backend.correlation.schemas import AnalyzeCorrelationRequest, AnalyzeCorrelationResponse
from backend.correlation.security import correlation_access_context, correlation_analysis_rate_limit
from backend.correlation.tasks import run_correlation_background
from backend.database import get_db

router = APIRouter(
    prefix=f"{API_PREFIX}/correlation",
    tags=["correlation"],
    dependencies=[Depends(correlation_access_context)],
)


class LegacyAnalyzeRequest(BaseModel):
    upload_id: str
    top_n: int = Field(default=50, ge=1, le=500)
    config_path: str | None = None


@router.post(
    "/analyze",
    response_model=AnalyzeCorrelationResponse | dict[str, Any],
    summary="Correlate failures with patterns across FA-FR-001 through FA-FR-005",
)
async def analyze_correlation(
    body: AnalyzeCorrelationRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(correlation_access_context),
    _rate_limit: None = Depends(correlation_analysis_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if body.top_n is not None:
        legacy = CorrelationService(CorrelationRepository(db))
        try:
            result = await legacy.analyze_upload(body.upload_id or "", top_n=body.top_n)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await db.commit()
        return result
    execution_id = str(uuid.uuid4())
    effective = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective.async_execution:
        config = CorrelationConfig.load()
        await ProductionCorrelationRepository(db).create_audit(
            analysis_id=execution_id,
            dataset_id=effective.dataset_id,
            upload_id=effective.upload_id,
            config_version=config.version,
            status="queued",
            actor=effective.actor,
            details={"incremental": effective.incremental, "requirement": "FA-FR-006"},
        )
        await db.commit()
        background_tasks.add_task(run_correlation_background, effective.model_dump(), execution_id)
        return {
            "execution_id": execution_id,
            "dataset_id": effective.dataset_id,
            "upload_id": effective.upload_id,
            "status": "queued",
            "config_version": config.version,
        }
    try:
        return await ProductionCorrelationService(db).execute(effective, execution_id=execution_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except CorrelationValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_CORRELATION_SOURCE", "issues": exc.issues},
        ) from exc
    except (ValueError, CorrelationComputationError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "CORRELATION_ANALYSIS_REJECTED", "message": str(exc)},
        ) from exc


@router.post("/legacy/analyze", include_in_schema=False)
async def analyze_legacy_correlation(
    body: LegacyAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Compatibility endpoint for the original record-only correlation report."""
    repo = CorrelationRepository(db)
    service = CorrelationService(repo, config_path=body.config_path)
    try:
        result = await service.analyze_upload(body.upload_id, top_n=body.top_n)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("", summary="Search immutable correlation results")
async def list_correlations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    pattern_id: str | None = Query(None, max_length=128),
    fault_type: str | None = Query(None, max_length=128),
    strength: str | None = Query(None, max_length=32),
    severity: str | None = Query(None, max_length=32),
    trend: str | None = Query(None, max_length=32),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionCorrelationRepository(db).list_correlations(
        limit=limit,
        offset=offset,
        pattern_id=pattern_id,
        fault_type=fault_type,
        strength=strength,
        severity=severity,
        trend=trend,
        analysis_id=analysis_id,
    )
    legacy_runs = await CorrelationRepository(db).list_runs(limit=min(limit, 200))
    return {
        "correlations": [serialize_correlation(row) for row in rows],
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "pattern_count": run.pattern_count,
                "top_correlation_score": run.top_correlation_score,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in legacy_runs
        ],
    }


@router.get("/history", summary="Immutable correlation execution and benchmark history")
async def correlation_history(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionCorrelationRepository(db).history(limit)
    return {
        "history": [
            {
                "execution_id": row.analysis_id,
                "dataset_id": row.dataset_id,
                "upload_id": row.upload_id,
                "status": row.status,
                "config_version": row.config_version,
                "source_record_count": row.source_record_count,
                "pattern_count": row.pattern_count,
                "correlation_count": row.correlation_count,
                "processing_ms": row.processing_ms,
                "benchmark_metrics": row.benchmark_metrics,
                "upstream_execution_ids": row.upstream_execution_ids,
                "errors": row.errors,
                "warnings": row.warnings,
                "actor": row.actor,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            }
            for row in rows
        ]
    }


@router.get("/statistics", summary="Latest correlation matrix and aggregate statistics")
async def correlation_statistics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await ProductionCorrelationRepository(db).latest_statistics()


@router.get("/trends", summary="Correlation coefficient trends")
async def correlation_trends(
    limit: int = Query(300, ge=1, le=1000),
    correlation_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionCorrelationRepository(db).trends(limit, correlation_id)
    return {
        "trends": [
            {
                "correlation_id": row.correlation_id,
                "analysis_id": row.analysis_id,
                "pattern_id": row.pattern_id,
                "fault_type": row.fault_type,
                "trend_status": row.trend_status,
                "current_coefficient": row.current_coefficient,
                "historical_coefficient": row.historical_coefficient,
                "absolute_change": row.absolute_change,
                "time_series": row.time_series,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/matrix")
async def correlation_matrix(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if run_id:
        repo = CorrelationRepository(db)
        service = CorrelationService(repo)
        try:
            return await service.get_matrix(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return (await ProductionCorrelationRepository(db).latest_statistics()).get("matrix", {})


@router.get("/network")
async def correlation_network(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if run_id:
        repo = CorrelationRepository(db)
        service = CorrelationService(repo)
        try:
            return await service.get_network(run_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    return (await ProductionCorrelationRepository(db).latest_statistics()).get("relationship_graph", {})


@router.get("/{correlation_id}", summary="Traceable correlation drill-down")
async def correlation_detail(
    correlation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ProductionCorrelationRepository(db)
    row = await repo.get_correlation(correlation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Correlation not found")
    trends = await repo.trends(100, correlation_id)
    recommendations = await repo.recommendations(correlation_id)
    return {
        "correlation": serialize_correlation(row),
        "traceability": {
            "dataset_id": row.dataset_id,
            "upload_id": row.upload_id,
            "detection_execution_id": row.detection_execution_id,
            "computation_id": row.computation_id,
            "classification_execution_id": row.classification_execution_id,
            "recurrence_analysis_id": row.recurrence_analysis_id,
            "recurrence_id": row.recurrence_id,
            "canonical_correlation_key": row.canonical_correlation_key,
            **dict(row.metadata_json or {}),
        },
        "trends": [
            {
                "trend_status": item.trend_status,
                "current_coefficient": item.current_coefficient,
                "historical_coefficient": item.historical_coefficient,
                "time_series": item.time_series,
            }
            for item in trends
        ],
        "engineering_recommendations": [
            {
                "recommendation_id": item.recommendation_id,
                "recommendation_code": item.recommendation_code,
                "priority": item.priority,
                "action": item.action,
                "rationale": item.rationale,
                "evidence": item.evidence,
            }
            for item in recommendations
        ],
        "downstream_export": {
            "schema_version": "fa-fr-006.v1",
            "correlation_id": row.correlation_id,
            "pattern_id": row.pattern_id,
            "fault_type": row.fault_type,
            "correlation_coefficient": row.correlation_coefficient,
            "correlation_strength": row.correlation_strength,
            "confidence_score": row.confidence_score,
            "severity": row.severity,
            "trend_status": row.trend_status,
            "hotspot_location": row.hotspot_location,
            "recommendation_codes": [item.recommendation_code for item in recommendations],
        },
    }
