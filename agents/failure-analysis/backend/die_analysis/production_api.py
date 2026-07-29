"""Production REST API for FA-FR-007 die-level failure analysis."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.die_analysis.die_repository import DieAnalysisRepository
from backend.die_analysis.die_service import DieAnalysisService
from backend.die_analysis.production_engine import (
    DieAnalysisConfig,
    DieComputationError,
)
from backend.die_analysis.production_repository import ProductionDieAnalysisRepository
from backend.die_analysis.production_service import (
    DieValidationError,
    ProductionDieAnalysisService,
    serialize_die,
)
from backend.die_analysis.schemas import AnalyzeDieRequest, AnalyzeDieResponse
from backend.die_analysis.security import die_access_context, die_analysis_rate_limit
from backend.die_analysis.tasks import run_die_analysis_background

router = APIRouter(
    prefix=f"{API_PREFIX}/die-analysis",
    tags=["die-analysis"],
    dependencies=[Depends(die_access_context)],
)


@router.post(
    "/analyze",
    response_model=AnalyzeDieResponse | dict[str, Any],
    summary="Aggregate every die with FA-FR-001 through FA-FR-006 lineage gates",
)
async def analyze_die_level(
    body: AnalyzeDieRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(die_access_context),
    _rate_limit: None = Depends(die_analysis_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if body.legacy:
        legacy = DieAnalysisService(DieAnalysisRepository(db))
        try:
            result = await legacy.analyze_upload(body.upload_id or "")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await db.commit()
        return result

    execution_id = str(uuid.uuid4())
    effective = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective.async_execution:
        config = DieAnalysisConfig.load()
        await ProductionDieAnalysisRepository(db).create_audit(
            analysis_id=execution_id,
            dataset_id=effective.dataset_id,
            upload_id=effective.upload_id,
            config_version=config.version,
            status="queued",
            actor=effective.actor,
            details={"incremental": effective.incremental, "requirement": "FA-FR-007"},
        )
        await db.commit()
        background_tasks.add_task(
            run_die_analysis_background, effective.model_dump(), execution_id
        )
        return {
            "execution_id": execution_id,
            "dataset_id": effective.dataset_id,
            "upload_id": effective.upload_id,
            "status": "queued",
            "config_version": config.version,
        }
    try:
        return await ProductionDieAnalysisService(db).execute(
            effective, execution_id=execution_id
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except DieValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_DIE_ANALYSIS_SOURCE", "issues": exc.issues},
        ) from exc
    except (ValueError, DieComputationError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "DIE_ANALYSIS_REJECTED", "message": str(exc)},
        ) from exc


@router.get("", summary="Search immutable die-level analysis results")
async def list_die_analyses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    lot_id: str | None = Query(None, max_length=128),
    wafer_id: str | None = Query(None, max_length=128),
    die_id: str | None = Query(None, max_length=128),
    severity: str | None = Query(None, max_length=32),
    is_failing: bool | None = Query(None),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionDieAnalysisRepository(db).list_dies(
        limit=limit,
        offset=offset,
        lot_id=lot_id,
        wafer_id=wafer_id,
        die_id=die_id,
        severity=severity,
        is_failing=is_failing,
        analysis_id=analysis_id,
    )
    legacy_runs = await DieAnalysisRepository(db).list_runs(limit=min(limit, 200))
    return {
        "dies": [serialize_die(row) for row in rows],
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "total_dies": run.total_dies,
                "failing_dies": run.failing_dies,
                "overall_yield_pct": run.overall_yield_pct,
                "hotspot_count": run.hotspot_count,
                "cluster_count": run.cluster_count,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in legacy_runs
        ],
    }


@router.get("/hotspots", summary="Die-level spatial hotspots")
async def die_hotspots(
    limit: int = Query(300, ge=1, le=1000),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionDieAnalysisRepository(db).hotspots(
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
                "coordinates": row.coordinates,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/clusters", summary="Deterministic die failure clusters")
async def die_clusters(
    limit: int = Query(300, ge=1, le=1000),
    analysis_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionDieAnalysisRepository(db).clusters(
        limit=limit, analysis_id=analysis_id
    )
    return {
        "clusters": [
            {
                "cluster_id": row.cluster_id,
                "analysis_id": row.analysis_id,
                "lot_id": row.lot_id,
                "wafer_id": row.wafer_id,
                "algorithm": row.algorithm,
                "die_count": row.die_count,
                "failure_count": row.failure_count,
                "density": row.density,
                "centroid_x": row.centroid_x,
                "centroid_y": row.centroid_y,
                "severity": row.severity,
                "member_die_ids": row.member_die_ids,
                "coordinates": row.coordinates,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/statistics", summary="Latest die aggregate statistics")
async def die_statistics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await ProductionDieAnalysisRepository(db).latest_statistics()


@router.get("/{die_result_id}", summary="Traceable die-level drill-down")
async def die_detail(
    die_result_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ProductionDieAnalysisRepository(db)
    row = await repo.get_die(die_result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Die analysis result not found")
    recommendations = [
        item
        for item in await repo.recommendations(row.analysis_id)
        if (item.evidence or {}).get("die_id") == row.die_id
        or item.pattern_id == row.die_id
        or item.pattern_id == row.dominant_pattern_id
    ]
    return {
        "die": serialize_die(row),
        "traceability": {
            "dataset_id": row.dataset_id,
            "upload_id": row.upload_id,
            "detection_execution_id": row.detection_execution_id,
            "computation_id": row.computation_id,
            "classification_execution_id": row.classification_execution_id,
            "recurrence_analysis_id": row.recurrence_analysis_id,
            "correlation_analysis_id": row.correlation_analysis_id,
            "canonical_die_key": row.canonical_die_key,
            "lot_comparison": row.lot_comparison,
            "wafer_comparison": row.wafer_comparison,
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
            "schema_version": "fa-fr-007.v1",
            "die_result_id": row.die_result_id,
            "lot_id": row.lot_id,
            "wafer_id": row.wafer_id,
            "die_id": row.die_id,
            "failure_count": row.failure_count,
            "failure_density": row.failure_density,
            "health_score": row.health_score,
            "severity": row.severity,
            "confidence_score": row.confidence_score,
            "trend_status": row.trend_status,
            "hotspot_id": row.hotspot_id,
            "cluster_id": row.cluster_id,
            "recommendation_codes": [
                item.recommendation_code for item in recommendations
            ],
        },
    }
