"""REST API for FA-FR-005 recurring failure detection."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.recurring.recurring_repository import RecurringRepository
from backend.recurring.recurring_service import RecurringService

router = APIRouter(prefix=f"{API_PREFIX}/recurring", tags=["recurring"])


class AnalyzeRequest(BaseModel):
    upload_id: str
    incremental: bool = False
    config_path: str | None = None


@router.post("/analyze")
async def analyze_recurring_failures(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Detect recurring failures across lots, wafers, dies, devices, and time."""
    repo = RecurringRepository(db)
    service = RecurringService(repo, config_path=body.config_path)
    try:
        result = await service.analyze_upload(
            body.upload_id,
            incremental=body.incremental,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return result


@router.get("")
async def list_recurring_runs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = RecurringRepository(db)
    runs = await repo.list_runs(limit=limit)
    return {
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "recurring_count": run.recurring_count,
                "impacted_lot_count": run.impacted_lot_count,
                "alert_count": run.alert_count,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    }


@router.get("/dashboard")
async def recurring_dashboard(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = RecurringRepository(db)
    run = await repo.get_latest_or(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No recurring analysis runs found")

    return {
        "run_id": run.id,
        "upload_id": run.upload_id,
        "dashboard": run.dashboard_json,
        "summary": run.report_json.get("classification_summary", {}),
    }
