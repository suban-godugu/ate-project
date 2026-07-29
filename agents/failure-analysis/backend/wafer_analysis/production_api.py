"""Production REST API for FA-FR-008 wafer-level failure analysis."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.wafer_analysis.production_engine import (
    WaferAnalysisConfig,
    WaferComputationError,
)
from backend.wafer_analysis.production_repository import ProductionWaferAnalysisRepository
from backend.wafer_analysis.production_service import (
    ProductionWaferAnalysisService,
    WaferValidationError,
    serialize_wafer,
)
from backend.wafer_analysis.schemas import AnalyzeWaferRequest, AnalyzeWaferResponse
from backend.wafer_analysis.security import wafer_access_context, wafer_analysis_rate_limit
from backend.wafer_analysis.tasks import run_wafer_analysis_background
from backend.wafer_analysis.wafer_repository import WaferAnalysisRepository
from backend.wafer_analysis.wafer_service import WaferAnalysisService

router = APIRouter(
    prefix=f"{API_PREFIX}/wafer-analysis",
    tags=["wafer-analysis"],
    dependencies=[Depends(wafer_access_context)],
)


@router.post(
    "/analyze",
    response_model=AnalyzeWaferResponse | dict[str, Any],
    summary="Aggregate every wafer with FA-FR-001 through FA-FR-007 lineage gates",
)
async def analyze_wafer_level(
    body: AnalyzeWaferRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(wafer_access_context),
    _rate_limit: None = Depends(wafer_analysis_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if body.legacy:
        legacy = WaferAnalysisService(WaferAnalysisRepository(db))
        try:
            result = await legacy.analyze_upload(body.upload_id or "")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await db.commit()
        return result

    execution_id = str(uuid.uuid4())
    effective = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective.async_execution:
        config = WaferAnalysisConfig.load()
        await ProductionWaferAnalysisRepository(db).create_audit(
            analysis_id=execution_id,
            dataset_id=effective.dataset_id,
            upload_id=effective.upload_id,
            config_version=config.version,
            status="queued",
            actor=effective.actor,
            details={"incremental": effective.incremental, "requirement": "FA-FR-008"},
        )
        await db.commit()
        background_tasks.add_task(
            run_wafer_analysis_background, effective.model_dump(), execution_id
        )
        return {
            "execution_id": execution_id,
            "dataset_id": effective.dataset_id,
            "upload_id": effective.upload_id,
            "status": "queued",
            "config_version": config.version,
        }
    try:
        return await ProductionWaferAnalysisService(db).execute(
            effective, execution_id=execution_id
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except WaferValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_WAFER_ANALYSIS_SOURCE", "issues": exc.issues},
        ) from exc
    except (ValueError, WaferComputationError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "WAFER_ANALYSIS_REJECTED", "message": str(exc)},
        ) from exc


@router.get("", summary="Search immutable wafer-level analysis results")
async def list_wafer_analyses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    lot_id: str | None = Query(None, max_length=128),
    wafer_id: str | None = Query(None, max_length=128),
    severity: str | None = Query(None, max_length=32),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionWaferAnalysisRepository(db).list_wafers(
        limit=limit,
        offset=offset,
        lot_id=lot_id,
        wafer_id=wafer_id,
        severity=severity,
        analysis_id=analysis_id,
    )
    legacy_runs = await WaferAnalysisRepository(db).list_runs(limit=min(limit, 200))
    return {
        "wafers": [serialize_wafer(row) for row in rows],
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "total_wafers": run.total_wafers,
                "overall_yield_pct": run.overall_yield_pct,
                "outlier_wafer_count": run.outlier_wafer_count,
                "hotspot_count": run.hotspot_count,
                "cluster_count": run.cluster_count,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in legacy_runs
        ],
    }


@router.get("/hotspots", summary="Wafer-level spatial hotspots")
async def wafer_hotspots(
    limit: int = Query(300, ge=1, le=1000),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionWaferAnalysisRepository(db).hotspots(
        limit=limit, analysis_id=analysis_id
    )
    return {
        "hotspots": [
            {
                "hotspot_id": row.hotspot_id,
                "analysis_id": row.analysis_id,
                "lot_id": row.lot_id,
                "wafer_id": row.wafer_id,
                "center_x": row.center_x,
                "center_y": row.center_y,
                "radius": row.radius,
                "die_count": row.die_count,
                "failure_count": row.failure_count,
                "density": row.density,
                "severity": row.severity,
                "confidence_score": row.confidence_score,
                "member_die_ids": row.member_die_ids,
                "density_grid": row.density_grid,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/statistics", summary="Latest wafer aggregate statistics")
async def wafer_statistics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await ProductionWaferAnalysisRepository(db).latest_statistics()


@router.get("/yield", summary="Wafer yield metrics and historical trends")
async def wafer_yield(
    limit: int = Query(300, ge=1, le=1000),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionWaferAnalysisRepository(db).yield_metrics(
        limit=limit, analysis_id=analysis_id
    )
    return {
        "yield_metrics": [
            {
                "wafer_result_id": row.wafer_result_id,
                "analysis_id": row.analysis_id,
                "lot_id": row.lot_id,
                "wafer_id": row.wafer_id,
                "yield_pct": row.yield_pct,
                "historical_yield_pct": row.historical_yield_pct,
                "yield_delta": row.yield_delta,
                "trend_status": row.trend_status,
                "lot_yield_pct": row.lot_yield_pct,
                "details": row.details,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/{wafer_result_id}", summary="Traceable wafer-level drill-down")
async def wafer_detail(
    wafer_result_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ProductionWaferAnalysisRepository(db)
    row = await repo.get_wafer(wafer_result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Wafer analysis result not found")
    recommendations = [
        item
        for item in await repo.recommendations(row.analysis_id)
        if (item.evidence or {}).get("wafer_id") == row.wafer_id
        or item.pattern_id == row.wafer_id
    ]
    return {
        "wafer": serialize_wafer(row),
        "traceability": {
            "dataset_id": row.dataset_id,
            "upload_id": row.upload_id,
            "detection_execution_id": row.detection_execution_id,
            "computation_id": row.computation_id,
            "classification_execution_id": row.classification_execution_id,
            "recurrence_analysis_id": row.recurrence_analysis_id,
            "correlation_analysis_id": row.correlation_analysis_id,
            "die_analysis_id": row.die_analysis_id,
            "canonical_wafer_key": row.canonical_wafer_key,
            "radial_distribution": row.radial_distribution,
            "lot_comparison": row.lot_comparison,
            **dict(row.metadata_json or {}),
        },
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
            "schema_version": "fa-fr-008.v1",
            "wafer_result_id": row.wafer_result_id,
            "lot_id": row.lot_id,
            "wafer_id": row.wafer_id,
            "yield_pct": row.yield_pct,
            "failure_density": row.failure_density,
            "health_score": row.health_score,
            "severity": row.severity,
            "confidence_score": row.confidence_score,
            "trend_status": row.trend_status,
            "recommendation_codes": [
                item.recommendation_code for item in recommendations
            ],
        },
    }
