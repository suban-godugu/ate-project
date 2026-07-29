"""REST API for legacy FA-FR-007 die-level failure analytics.

Compatibility path: production FA-FR-007 lives at ``/api/v1/die-analysis``.
This router preserves the original ``/api/v1/die`` contract.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.die_analysis.die_repository import DieAnalysisRepository
from backend.die_analysis.die_service import DieAnalysisService

router = APIRouter(prefix=f"{API_PREFIX}/die", tags=["die-analysis-legacy"])


class AnalyzeRequest(BaseModel):
    upload_id: str
    config_path: str | None = None


@router.post("/analyze")
async def analyze_die_level(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run die-level spatial failure analytics on normalized upload data."""
    repo = DieAnalysisRepository(db)
    service = DieAnalysisService(repo, config_path=body.config_path)
    try:
        result = await service.analyze_upload(body.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("")
async def list_die_analyses(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = DieAnalysisRepository(db)
    runs = await repo.list_runs(limit=limit)
    return {
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
            for run in runs
        ]
    }


@router.get("/heatmap")
async def die_heatmap(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = DieAnalysisRepository(db)
    service = DieAnalysisService(repo)
    try:
        return await service.get_heatmap(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/hotspots")
async def die_hotspots(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = DieAnalysisRepository(db)
    service = DieAnalysisService(repo)
    try:
        return await service.get_hotspots(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/statistics")
async def die_statistics(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = DieAnalysisRepository(db)
    service = DieAnalysisService(repo)
    try:
        return await service.get_statistics(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
