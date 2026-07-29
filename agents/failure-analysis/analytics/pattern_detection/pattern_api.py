"""REST API for FA-FR-002 pattern detection."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.bridge import test_records_to_die_logs
from analytics.pattern_detection.pattern_engine import PatternEngine
from analytics.pattern_detection.detection_repository import DetectionRepository
from analytics.pattern_detection.detection_service import (
    DetectionService,
    DetectionValidationError,
    serialize_pattern,
)
from analytics.pattern_detection.pattern_repository import PatternRepository
from analytics.pattern_detection.schemas import (
    DetectPatternsRequest,
    DetectPatternsResponse,
)
from analytics.pattern_detection.tasks import run_detection_background
from backend.config import API_PREFIX
from backend.database import get_db

router = APIRouter(prefix=f"{API_PREFIX}/patterns", tags=["patterns"])


class AnalyzeRequest(BaseModel):
    upload_id: str | None = None
    top_n: int = Field(default=50, ge=1, le=500)


@router.post(
    "/detect",
    response_model=DetectPatternsResponse,
    summary="Detect known, recurring, and unknown failure patterns",
)
async def detect_patterns(
    body: DetectPatternsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute only against completed FA-FR-001 normalized sources."""
    execution_id = str(uuid.uuid4())
    if body.async_execution:
        background_tasks.add_task(
            run_detection_background, body.model_dump(), execution_id
        )
        return {
            "execution_id": execution_id,
            "dataset_id": body.dataset_id,
            "upload_id": body.upload_id,
            "status": "queued",
            "patterns": [],
        }
    try:
        return await DetectionService(db).execute(body, execution_id=execution_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)}) from exc
    except DetectionValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_NORMALIZED_DATASET", "issues": exc.issues},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "SOURCE_NOT_READY", "message": str(exc)},
        ) from exc


@router.post("/analyze")
async def analyze_patterns(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run full pattern detection pipeline on normalized upload data."""
    engine = PatternEngine()
    repo = PatternRepository(db)

    test_records = []
    if body.upload_id:
        test_records = await repo.load_test_records(body.upload_id)
        if not test_records:
            raise HTTPException(status_code=404, detail="No records found for upload_id")

    die_logs = test_records_to_die_logs(test_records) if test_records else []
    report = engine.analyze(
        die_logs=die_logs,
        test_records=test_records or None,
        upload_id=body.upload_id,
    )
    report["pattern_ranking"] = report["pattern_ranking"][: body.top_n]
    run = await repo.save_analysis(report)
    await db.commit()

    return {
        "analysis_id": run.id,
        "upload_id": body.upload_id,
        "status": run.status,
        "processing_ms": report["processing_ms"],
        "meets_performance_target": report["meets_performance_target"],
        "failure_pattern_report": {
            "failure_count": report["failure_count"],
            "unique_patterns": report["unique_patterns"],
            "dominant_failure_modes": report["dominant_failure_modes"],
            "failure_distribution": report["failure_distribution"],
            "clusters": report["clusters"],
            "anomalies": report["anomalies"],
        },
        "pattern_ranking": report["pattern_ranking"],
        "pattern_heatmap": report["pattern_heatmap"],
        "similar_pattern_lists": report["similar_pattern_lists"],
        "detection_accuracy": report["detection_accuracy"],
    }


@router.get("", summary="Search detected failure patterns")
async def list_pattern_analyses(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = Query(None),
    severity: str | None = Query(None),
    search: str | None = Query(None, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    production_repo = DetectionRepository(db)
    patterns = await production_repo.list_patterns(
        limit=limit,
        offset=offset,
        category=category,
        severity=severity,
        query=search,
    )
    # Keep legacy analysis summaries in the response for downstream compatibility.
    runs = await PatternRepository(db).list_analyses(limit=limit)
    return {
        "patterns": [serialize_pattern(row) for row in patterns],
        "analyses": [
            {
                "analysis_id": run.id,
                "upload_id": run.upload_id,
                "status": run.status,
                "failure_count": run.failure_count,
                "unique_patterns": run.unique_patterns,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    }


@router.get("/statistics", summary="Pattern detection summary and distribution")
async def pattern_statistics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await DetectionRepository(db).statistics()


@router.get("/history", summary="Detection execution and audit history")
async def pattern_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await DetectionRepository(db).histories(limit)
    return {
        "history": [
            {
                "id": row.id,
                "execution_id": row.analysis_id,
                "dataset_id": row.dataset_id,
                "upload_id": row.upload_id,
                "status": row.execution_status,
                "rule_set_version": row.rule_set_version,
                "pattern_count": row.pattern_count,
                "source_record_count": row.source_record_count,
                "processing_ms": row.processing_ms,
                "confidence_distribution": row.confidence_distribution,
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


@router.get("/top")
async def top_patterns(
    analysis_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = PatternRepository(db)
    patterns = await repo.top_patterns(analysis_id=analysis_id, limit=limit)
    return {
        "patterns": [
            {
                "id": row.id,
                "analysis_id": row.analysis_id,
                "pattern_id": row.pattern_id,
                "rank": row.rank,
                "rank_score": row.rank_score,
                "confidence": row.confidence,
                "failure_count": row.failure_count,
                "cluster_id": row.cluster_id,
                "is_anomaly": bool(row.is_anomaly),
                "details": row.payload,
            }
            for row in patterns
        ]
    }


@router.get("/{pattern_row_id}")
async def get_pattern_detail(
    pattern_row_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    bundle = await DetectionRepository(db).get_pattern_bundle(pattern_row_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Pattern not found")
    row = bundle["pattern"]
    repo = PatternRepository(db)
    analysis = await repo.get_analysis(row.analysis_id)
    similar = []
    if analysis:
        similar = analysis.report_json.get("similar_pattern_lists", {}).get(row.pattern_id, [])
    return {
        "id": row.id,
        "analysis_id": row.analysis_id,
        "pattern_id": row.pattern_id,
        "rank": row.rank,
        "confidence": row.confidence,
        "confidence_breakdown": row.payload.get("confidence_breakdown", {}),
        "failure_count": row.failure_count,
        "cluster_id": row.cluster_id,
        "is_anomaly": bool(row.is_anomaly),
        "similar_patterns": similar,
        "details": row.payload,
        "pattern_name": row.pattern_name,
        "pattern_category": row.pattern_category,
        "pattern_frequency": row.pattern_frequency,
        "detection_method": row.detection_method,
        "severity_level": row.severity_level,
        "affected_devices": row.affected_devices,
        "affected_dies": row.affected_dies,
        "affected_wafers": row.affected_wafers,
        "affected_lots": row.affected_lots,
        "engineering_explanation": row.engineering_explanation,
        "occurrences": [
            {
                "id": item.id,
                "source_record_id": item.source_record_id,
                "lot_id": item.lot_id,
                "wafer_id": item.wafer_id,
                "die_id": item.die_id,
                "device_id": item.device_id,
                "x": item.x,
                "y": item.y,
                "evidence": item.evidence,
            }
            for item in bundle["occurrences"]
        ],
        "confidence_record": (
            {
                "composite_score": bundle["confidence"].composite_score,
                "rule_score": bundle["confidence"].rule_score,
                "statistical_score": bundle["confidence"].statistical_score,
                "similarity_score": bundle["confidence"].similarity_score,
                "threshold": bundle["confidence"].threshold,
                "passed_threshold": bundle["confidence"].passed_threshold,
                "breakdown": bundle["confidence"].breakdown,
            }
            if bundle["confidence"]
            else None
        ),
    }
