"""REST API for FA-FR-008 wafer-level failure analytics."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.wafer_analysis.wafer_repository import WaferAnalysisRepository
from backend.wafer_analysis.wafer_service import WaferAnalysisService

router = APIRouter(prefix=f"{API_PREFIX}/wafer", tags=["wafer-analysis"])


class AnalyzeRequest(BaseModel):
    upload_id: str
    config_path: str | None = None


@router.post("/analyze")
async def analyze_wafer_level(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run wafer-level spatial failure analytics on normalized upload data."""
    repo = WaferAnalysisRepository(db)
    service = WaferAnalysisService(repo, config_path=body.config_path)
    try:
        result = await service.analyze_upload(body.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("")
async def list_wafer_analyses(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = WaferAnalysisRepository(db)
    runs = await repo.list_runs(limit=limit)
    return {
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
            for run in runs
        ]
    }


@router.get("/map")
async def wafer_map(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = WaferAnalysisRepository(db)
    service = WaferAnalysisService(repo)
    try:
        return await service.get_map(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/hotspots")
async def wafer_hotspots(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = WaferAnalysisRepository(db)
    service = WaferAnalysisService(repo)
    try:
        return await service.get_hotspots(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/statistics")
async def wafer_statistics(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = WaferAnalysisRepository(db)
    service = WaferAnalysisService(repo)
    try:
        return await service.get_statistics(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
