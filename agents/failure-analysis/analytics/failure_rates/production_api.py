"""Production REST API for FA-FR-003."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.failure_rates.computation_engine import FailureRateComputationError
from analytics.failure_rates.production_repository import (
    ProductionFailureRateRepository,
)
from analytics.failure_rates.production_service import (
    FailureRateValidationError,
    ProductionFailureRateService,
    serialize_metric,
)
from analytics.failure_rates.schemas import (
    ComputeFailureRatesRequest,
    ComputeFailureRatesResponse,
)
from analytics.failure_rates.tasks import run_failure_rate_background
from backend.config import API_PREFIX
from backend.database import get_db

router = APIRouter(prefix=f"{API_PREFIX}/failure-rate", tags=["failure-rate"])


@router.post(
    "/compute",
    response_model=ComputeFailureRatesResponse,
    summary="Compute versioned pattern failure rates",
)
async def compute_failure_rates(
    body: ComputeFailureRatesRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    execution_id = str(uuid.uuid4())
    if body.async_execution:
        background_tasks.add_task(
            run_failure_rate_background, body.model_dump(), execution_id
        )
        return {
            "execution_id": execution_id,
            "dataset_id": body.dataset_id,
            "upload_id": body.upload_id,
            "detection_execution_id": body.detection_execution_id or "pending",
            "status": "queued",
        }
    try:
        return await ProductionFailureRateService(db).execute(
            body, execution_id=execution_id
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except FailureRateValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_COMPUTATION_SOURCE", "issues": exc.issues},
        ) from exc
    except (ValueError, FailureRateComputationError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "COMPUTATION_REJECTED", "message": str(exc)},
        ) from exc


@router.get("", summary="Search persisted failure-rate metrics")
async def list_failure_rates(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    pattern_id: str | None = Query(None, max_length=128),
    aggregation_level: str | None = Query(None, max_length=32),
    computation_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionFailureRateRepository(db).list_metrics(
        limit=limit,
        offset=offset,
        pattern_id=pattern_id,
        level=aggregation_level,
        computation_id=computation_id,
    )
    return {"metrics": [serialize_metric(row) for row in rows]}


@router.get("/trends", summary="Historical pattern trend analysis")
async def failure_rate_trends(
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionFailureRateRepository(db).trends(limit)
    return {
        "trends": [
            {
                "id": row.id,
                "computation_id": row.computation_id,
                "pattern_id": row.pattern_id,
                "aggregation_level": row.aggregation_level,
                "aggregation_key": row.aggregation_key,
                "trend_direction": row.trend_direction,
                "current_percentage": row.current_percentage,
                "moving_average": row.moving_average,
                "baseline_percentage": row.baseline_percentage,
                "absolute_change": row.absolute_change,
                "relative_change": row.relative_change,
                "abnormal_increase": row.abnormal_increase,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/statistics", summary="Failure-rate summary statistics and benchmarks")
async def failure_rate_statistics(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await ProductionFailureRateRepository(db).statistics()


@router.get("/history", summary="Computation execution and audit history")
async def computation_history(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionFailureRateRepository(db).histories(limit)
    return {
        "history": [
            {
                "id": row.id,
                "execution_id": row.computation_id,
                "dataset_id": row.dataset_id,
                "upload_id": row.upload_id,
                "detection_execution_id": row.detection_execution_id,
                "status": row.status,
                "formula_version": row.formula_version,
                "aggregation_levels": row.aggregation_levels,
                "window_size": row.window_size,
                "source_record_count": row.source_record_count,
                "pattern_count": row.pattern_count,
                "metric_count": row.metric_count,
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


@router.get("/{pattern_id}", summary="Failure-rate history for a pattern")
async def pattern_failure_rates(
    pattern_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionFailureRateRepository(db).get_pattern_metrics(pattern_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Pattern failure rate not found")
    return {
        "pattern_id": pattern_id,
        "metrics": [serialize_metric(row) for row in rows],
    }
