"""REST API for FA-FR-009 AI root cause prediction."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.root_cause.root_cause_repository import RootCauseRepository
from backend.root_cause.root_cause_service import RootCauseService

router = APIRouter(prefix=f"{API_PREFIX}/root-cause", tags=["root-cause"])


class PredictRequest(BaseModel):
    upload_id: str
    config_path: str | None = None


@router.post("/predict")
async def predict_root_cause(
    body: PredictRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run AI root cause prediction on normalized upload data."""
    repo = RootCauseRepository(db)
    service = RootCauseService(repo, config_path=body.config_path)
    try:
        result = await service.predict_upload(body.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("")
async def list_root_cause_runs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = RootCauseRepository(db)
    runs = await repo.list_runs(limit=limit)
    return {
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "total_predictions": run.total_predictions,
                "average_confidence": run.average_confidence,
                "high_confidence_count": run.high_confidence_count,
                "ml_model_trained": bool(run.ml_model_trained),
                "processing_ms": run.processing_ms,
                "semantic_search_ms": run.semantic_search_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    }


@router.get("/history")
async def root_cause_history(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = RootCauseRepository(db)
    service = RootCauseService(repo)
    try:
        return await service.get_history(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/recommendations")
async def root_cause_recommendations(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = RootCauseRepository(db)
    service = RootCauseService(repo)
    try:
        return await service.get_recommendations(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
