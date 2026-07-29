"""REST API for FA-FR-004 fault classification."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.classification.classification_repository import ClassificationRepository
from backend.classification.classification_service import ClassificationService
from backend.config import API_PREFIX
from backend.database import get_db

router = APIRouter(prefix=f"{API_PREFIX}/classification", tags=["classification"])


class AnalyzeRequest(BaseModel):
    upload_id: str
    enable_ml: bool = True
    enable_llm: bool = True
    taxonomy_path: str | None = None


@router.post("/analyze")
async def analyze_classification(
    body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run hybrid fault classification on normalized upload data."""
    repo = ClassificationRepository(db)
    service = ClassificationService(
        repo,
        taxonomy_path=body.taxonomy_path,
        enable_ml=body.enable_ml,
        enable_llm=body.enable_llm,
    )
    try:
        result = await service.analyze_upload(body.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await db.commit()
    return {
        **result,
        "fault_classification_report": {
            "classified_faults": result["classified_faults"],
            "die_classifications": result["die_classifications"],
            "category_summary": result["category_summary"],
        },
    }


@router.get("")
async def list_classifications(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ClassificationRepository(db)
    runs = await repo.list_runs(limit=limit)
    return {
        "runs": [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "total_faults": run.total_faults,
                "unique_categories": run.unique_categories,
                "dominant_category": run.dominant_category,
                "estimated_accuracy_pct": run.estimated_accuracy_pct,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    }


@router.get("/statistics")
async def classification_statistics(
    run_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ClassificationRepository(db)
    service = ClassificationService(repo)
    try:
        return await service.get_statistics(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{fault_id}")
async def get_classified_fault(
    fault_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = ClassificationRepository(db)
    fault = await repo.get_fault(fault_id)
    if fault is None:
        raise HTTPException(status_code=404, detail="Classified fault not found")

    payload = dict(fault.payload)
    return {
        "fault_id": fault.id,
        "run_id": fault.run_id,
        "fault_category": fault.fault_category,
        "classification_confidence": fault.classification_confidence,
        "method": fault.method,
        "lot_id": fault.lot_id,
        "wafer_id": fault.wafer_id,
        "die_id": fault.die_id,
        "pattern_id": fault.pattern_id,
        "supporting_parameters": payload.get("supporting_parameters", {}),
        "failure_signature": payload.get("failure_signature", ""),
        "engineering_recommendation": payload.get("engineering_recommendation", ""),
        "explanation": payload.get("explanation", ""),
        "confidence_breakdown": payload.get("confidence_breakdown", {}),
        "classification_detail": payload,
    }
