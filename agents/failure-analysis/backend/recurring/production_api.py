"""Production REST API for FA-FR-005 recurring failure analysis."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.recurring.production_engine import (
    RecurrenceComputationError,
    RecurrenceConfig,
)
from backend.recurring.production_repository import ProductionRecurrenceRepository
from backend.recurring.production_service import (
    ProductionRecurrenceService,
    RecurrenceValidationError,
    serialize_recurrence,
)
from backend.recurring.schemas import AnalyzeRecurrenceRequest, AnalyzeRecurrenceResponse
from backend.recurring.security import (
    recurrence_access_context,
    recurrence_analysis_rate_limit,
)
from backend.recurring.tasks import run_recurrence_background

router = APIRouter(
    prefix=f"{API_PREFIX}/recurrence",
    tags=["recurrence"],
    dependencies=[Depends(recurrence_access_context)],
)


@router.post(
    "/analyze",
    response_model=AnalyzeRecurrenceResponse,
    summary="Analyze recurring failures across versioned historical executions",
)
async def analyze_recurrence(
    body: AnalyzeRecurrenceRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(recurrence_access_context),
    _rate_limit: None = Depends(recurrence_analysis_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    execution_id = str(uuid.uuid4())
    effective_body = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective_body.async_execution:
        config = RecurrenceConfig.load()
        await ProductionRecurrenceRepository(db).create_audit(
            analysis_id=execution_id,
            dataset_id=effective_body.dataset_id,
            upload_id=effective_body.upload_id,
            detection_execution_id=effective_body.detection_execution_id,
            computation_id=effective_body.computation_id,
            status="queued",
            config_version=config.version,
            actor=effective_body.actor,
            details={
                "incremental": effective_body.incremental,
                "requirement": "FA-FR-005",
            },
        )
        await db.commit()
        background_tasks.add_task(
            run_recurrence_background, effective_body.model_dump(), execution_id
        )
        return {
            "execution_id": execution_id,
            "dataset_id": effective_body.dataset_id,
            "upload_id": effective_body.upload_id,
            "detection_execution_id": effective_body.detection_execution_id,
            "computation_id": effective_body.computation_id,
            "status": "queued",
            "config_version": config.version,
        }
    try:
        return await ProductionRecurrenceService(db).execute(
            effective_body, execution_id=execution_id
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except RecurrenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_RECURRENCE_SOURCE", "issues": exc.issues},
        ) from exc
    except (ValueError, RecurrenceComputationError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "RECURRENCE_ANALYSIS_REJECTED", "message": str(exc)},
        ) from exc


@router.get("", summary="Search immutable recurring failure results")
async def list_recurrences(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    pattern_id: str | None = Query(None, max_length=128),
    fault_type: str | None = Query(None, max_length=128),
    severity: str | None = Query(None, max_length=32),
    trend: str | None = Query(None, max_length=32),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionRecurrenceRepository(db).list_recurrences(
        limit=limit,
        offset=offset,
        pattern_id=pattern_id,
        fault_type=fault_type,
        severity=severity,
        trend=trend,
        analysis_id=analysis_id,
    )
    return {"recurrences": [serialize_recurrence(row) for row in rows]}


@router.get("/trends", summary="Recurrence frequency and direction history")
async def recurrence_trends(
    limit: int = Query(300, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionRecurrenceRepository(db).trends(limit)
    return {
        "trends": [
            {
                "id": row.id,
                "recurrence_id": row.recurrence_id,
                "analysis_id": row.analysis_id,
                "pattern_id": row.pattern_id,
                "trend_direction": row.trend_direction,
                "current_frequency": row.current_frequency,
                "historical_frequency": row.historical_frequency,
                "absolute_change": row.absolute_change,
                "relative_change": row.relative_change,
                "newly_emerging": row.newly_emerging,
                "time_series": row.time_series,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/hotspots", summary="Recurring spatial failure hotspots")
async def recurrence_hotspots(
    limit: int = Query(300, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionRecurrenceRepository(db).hotspots(limit)
    return {
        "hotspots": [
            {
                "hotspot_id": row.hotspot_id,
                "recurrence_id": row.recurrence_id,
                "analysis_id": row.analysis_id,
                "pattern_id": row.pattern_id,
                "lot_id": row.lot_id,
                "wafer_id": row.wafer_id,
                "x": row.x,
                "y": row.y,
                "radius": row.radius,
                "occurrence_count": row.occurrence_count,
                "density": row.density,
                "confidence_score": row.confidence_score,
                "severity": row.severity,
                "coordinates": row.coordinates,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/history", summary="Immutable recurrence execution audit history")
async def recurrence_history(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionRecurrenceRepository(db).history(limit)
    return {
        "history": [
            {
                "id": row.id,
                "execution_id": row.analysis_id,
                "dataset_id": row.dataset_id,
                "upload_id": row.upload_id,
                "detection_execution_id": row.detection_execution_id,
                "computation_id": row.computation_id,
                "classification_execution_id": (row.details or {}).get(
                    "classification_execution_id"
                ),
                "action": row.action,
                "status": row.status,
                "config_version": row.config_version,
                "source_record_count": row.source_record_count,
                "pattern_count": row.pattern_count,
                "recurrence_count": row.recurrence_count,
                "processing_ms": row.processing_ms,
                "benchmark_metrics": row.benchmark_metrics,
                "errors": row.errors,
                "warnings": row.warnings,
                "actor": row.actor,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            }
            for row in rows
        ]
    }


@router.get("/statistics", summary="Recurrence summary and benchmark metrics")
async def recurrence_statistics(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await ProductionRecurrenceRepository(db).statistics()


@router.get("/{recurrence_id}", summary="Traceable recurrence detail")
async def recurrence_detail(
    recurrence_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ProductionRecurrenceRepository(db)
    row = await repo.get_recurrence(recurrence_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Recurrence not found")
    trends = await repo.trends_for_recurrence(recurrence_id)
    hotspots = await repo.hotspots_for_recurrence(recurrence_id)
    recommendations = await repo.recommendations(recurrence_id)
    return {
        "recurrence": serialize_recurrence(row),
        "traceability": {
            "dataset_id": row.dataset_id,
            "upload_id": row.upload_id,
            "detection_execution_id": row.detection_execution_id,
            "computation_id": row.computation_id,
            "classification_execution_id": row.classification_execution_id,
            "detected_pattern_id": row.detected_pattern_id,
            "canonical_recurrence_key": row.canonical_recurrence_key,
            "signature_hash": row.signature_hash,
            **dict(row.metadata_json or {}),
        },
        "trends": [
            {
                "trend_direction": item.trend_direction,
                "current_frequency": item.current_frequency,
                "historical_frequency": item.historical_frequency,
                "newly_emerging": item.newly_emerging,
                "time_series": item.time_series,
            }
            for item in trends
        ],
        "hotspots": [
            {
                "hotspot_id": item.hotspot_id,
                "x": item.x,
                "y": item.y,
                "radius": item.radius,
                "occurrence_count": item.occurrence_count,
                "coordinates": item.coordinates,
            }
            for item in hotspots
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
            "schema_version": "fa-fr-005.v1",
            "recurrence_id": row.recurrence_id,
            "canonical_recurrence_key": row.canonical_recurrence_key,
            "pattern_id": row.pattern_id,
            "fault_type": row.fault_type,
            "recurrence_percentage": row.recurrence_percentage,
            "confidence_score": row.confidence_score,
            "severity": row.severity,
            "trend_status": row.trend_direction,
            "hotspot_location": row.hotspot_location,
            "affected_devices": (row.metadata_json or {}).get("affected_devices", []),
            "affected_dies": (row.metadata_json or {}).get("affected_dies", []),
            "affected_wafers": (row.metadata_json or {}).get("affected_wafers", []),
            "affected_lots": (row.metadata_json or {}).get("affected_lots", []),
            "recommendation_codes": [
                item.recommendation_code for item in recommendations
            ],
        },
    }
