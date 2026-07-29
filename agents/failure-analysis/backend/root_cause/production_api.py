"""Production REST API for FA-FR-009 fault-type prediction."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.root_cause.production_engine import (
    FaultPredictionComputationError,
    FaultPredictionConfig,
)
from backend.root_cause.production_repository import ProductionFaultPredictionRepository
from backend.root_cause.production_service import (
    FaultPredictionValidationError,
    ProductionFaultPredictionService,
    serialize_prediction,
)
from backend.root_cause.root_cause_service import RootCauseService
from backend.root_cause.root_cause_repository import RootCauseRepository
from backend.root_cause.schemas import (
    PredictFaultRequest,
    PredictFaultResponse,
    PredictionFeedbackRequest,
)
from backend.root_cause.security import (
    fault_prediction_access_context,
    fault_prediction_rate_limit,
)
from backend.root_cause.tasks import run_fault_prediction_background

router = APIRouter(
    prefix=f"{API_PREFIX}/fault-prediction",
    tags=["fault-prediction"],
    dependencies=[Depends(fault_prediction_access_context)],
)


@router.post(
    "/predict",
    response_model=PredictFaultResponse | dict[str, Any],
    summary="Predict probable fault types with FA-FR-001 through FA-FR-008 lineage gates",
)
async def predict_fault_types(
    body: PredictFaultRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(fault_prediction_access_context),
    _rate_limit: None = Depends(fault_prediction_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if body.legacy:
        legacy = RootCauseService(RootCauseRepository(db), config_path=body.config_path)
        try:
            result = await legacy.predict_upload(body.upload_id or "")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await db.commit()
        return result

    execution_id = str(uuid.uuid4())
    effective = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective.async_execution:
        config = FaultPredictionConfig.load()
        await ProductionFaultPredictionRepository(db).create_audit(
            execution_id=execution_id,
            dataset_id=effective.dataset_id,
            upload_id=effective.upload_id,
            config_version=config.version,
            model_version=config.model_version,
            status="queued",
            actor=effective.actor,
            details={"incremental": effective.incremental, "requirement": "FA-FR-009"},
        )
        await db.commit()
        background_tasks.add_task(
            run_fault_prediction_background, effective.model_dump(), execution_id
        )
        return {
            "execution_id": execution_id,
            "dataset_id": effective.dataset_id,
            "upload_id": effective.upload_id,
            "status": "queued",
            "config_version": config.version,
            "model_version": config.model_version,
        }
    try:
        return await ProductionFaultPredictionService(db).execute(
            effective, execution_id=execution_id
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail={"code": "SOURCE_NOT_FOUND", "message": str(exc)},
        ) from exc
    except FaultPredictionValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_FAULT_PREDICTION_SOURCE", "issues": exc.issues},
        ) from exc
    except (ValueError, FaultPredictionComputationError) as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "FAULT_PREDICTION_REJECTED", "message": str(exc)},
        ) from exc


@router.get("", summary="Search immutable fault-type prediction results")
async def list_fault_predictions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    pattern_id: str | None = Query(None, max_length=128),
    execution_id: str | None = Query(None, max_length=36),
    predicted_fault_type: str | None = Query(None, max_length=128),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionFaultPredictionRepository(db).list_predictions(
        limit=limit,
        offset=offset,
        pattern_id=pattern_id,
        execution_id=execution_id,
        predicted_fault_type=predicted_fault_type,
    )
    legacy_runs = await RootCauseRepository(db).list_runs(limit=min(limit, 200))
    return {
        "predictions": [serialize_prediction(row) for row in rows],
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "total_predictions": run.total_predictions,
                "average_confidence": run.average_confidence,
                "high_confidence_count": run.high_confidence_count,
                "ml_model_trained": bool(run.ml_model_trained),
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in legacy_runs
        ],
    }


@router.get("/history", summary="Prediction history snapshots")
async def prediction_history(
    limit: int = Query(300, ge=1, le=1000),
    execution_id: str | None = Query(None, max_length=36),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionFaultPredictionRepository(db).history(
        limit=limit, execution_id=execution_id
    )
    return {
        "history": [
            {
                "prediction_id": row.prediction_id,
                "execution_id": row.execution_id,
                "pattern_id": row.pattern_id,
                "predicted_fault_type": row.predicted_fault_type,
                "confidence_score": row.confidence_score,
                "prediction_probability": row.prediction_probability,
                "snapshot_version": row.snapshot_version,
                "source_execution_ids": row.source_execution_ids,
                "details": row.details,
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
            }
            for row in rows
        ]
    }


@router.get("/statistics", summary="Latest fault prediction aggregate statistics")
async def prediction_statistics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await ProductionFaultPredictionRepository(db).latest_statistics()


@router.post("/feedback", summary="Submit engineering feedback for model learning")
async def prediction_feedback(
    body: PredictionFeedbackRequest,
    access: dict[str, str] = Depends(fault_prediction_access_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = ProductionFaultPredictionService(db)
    try:
        return await service.submit_feedback(
            prediction_id=body.prediction_id,
            validated_fault_type=body.validated_fault_type,
            feedback_status=body.feedback_status,
            engineer_notes=body.engineer_notes,
            learning_weight=body.learning_weight,
            actor=body.actor or access["actor"],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{prediction_id}", summary="Traceable fault prediction drill-down")
async def prediction_detail(
    prediction_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    row = await ProductionFaultPredictionRepository(db).get_prediction(prediction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Fault prediction not found")
    return {
        "prediction": serialize_prediction(row),
        "traceability": {
            "dataset_id": row.dataset_id,
            "upload_id": row.upload_id,
            "detection_execution_id": row.detection_execution_id,
            "computation_id": row.computation_id,
            "classification_execution_id": row.classification_execution_id,
            "recurrence_analysis_id": row.recurrence_analysis_id,
            "correlation_analysis_id": row.correlation_analysis_id,
            "die_analysis_id": row.die_analysis_id,
            "wafer_analysis_id": row.wafer_analysis_id,
            "canonical_prediction_key": row.canonical_prediction_key,
            **dict(row.metadata_json or {}),
        },
        "downstream_export": {
            "schema_version": "fa-fr-009.v1",
            "prediction_id": row.prediction_id,
            "pattern_id": row.pattern_id,
            "predicted_fault_type": row.predicted_fault_type,
            "confidence_score": row.confidence_score,
            "prediction_probability": row.prediction_probability,
            "disclaimer": (
                "Probable fault type only; not a definitive root cause diagnosis."
            ),
        },
    }
