"""Async FastAPI routers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from ..core.config import Settings, get_settings
from ..core.dependencies import get_optimization_service
from ..domain.models import OptimizationContext
from ..domain.schemas import (
    AnalyticsSummary,
    CompareRequest,
    HealthResponse,
    OptimizationRecommendation,
    OptimizeRequest,
    RecommendationListResponse,
)
from ..services.optimization_service import OptimizationService
from ..services.sample_data import SAMPLES

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        agent="test_optimization_recommendation",
        version=settings.app_version,
        llm_enabled=settings.llm_enabled,
        model=settings.llm_model if settings.llm_enabled else None,
        environment=settings.environment,
    )


@router.post("/optimize", response_model=OptimizationRecommendation)
async def optimize(
    request: OptimizeRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationRecommendation:
    return await service.optimize(request.context, persist=request.persist)


@router.post("/optimize/raw", response_model=OptimizationRecommendation)
async def optimize_raw(
    context: OptimizationContext,
    persist: bool = True,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationRecommendation:
    return await service.optimize(context, persist=persist)


@router.post("/optimize/sample/{name}", response_model=OptimizationRecommendation)
async def optimize_sample(
    name: str,
    persist: bool = True,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationRecommendation:
    factory = SAMPLES.get(name)
    if not factory:
        raise HTTPException(404, f"Unknown sample. Available: {list(SAMPLES)}")
    return await service.optimize(factory(), persist=persist)


@router.get("/samples")
async def list_samples() -> dict:
    return {"samples": list(SAMPLES.keys())}


@router.get("/inputs")
async def get_inputs(settings: Settings = Depends(get_settings)) -> dict:
    """Inventory of OptimizationContext JSON files under the shared input folder."""
    from ..services.input_registry import input_inventory

    return input_inventory(settings)


@router.post("/inputs/connect")
async def post_connect_inputs(
    persist: bool = True,
    settings: Settings = Depends(get_settings),
    service: OptimizationService = Depends(get_optimization_service),
) -> dict:
    """
    Validate OptimizationContext JSON inputs and run optimize on each.

    Inputs (under UPLOAD_INPUT_ROOT/test-optimization):
      *.json OptimizationContext files (e.g. low_risk_context.json)

    Outputs (under AGENT_OUTPUT_ROOT/test-optimization/recommendations):
      persisted recommendation JSON
    """
    from ..services.input_registry import connect_inputs

    result = await connect_inputs(service, settings, persist=persist)
    if result.get("status") == "missing_inputs":
        raise HTTPException(status_code=400, detail=result)
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result)
    return result


@router.get("/recommendations", response_model=RecommendationListResponse)
async def list_recommendations(
    q: Optional[str] = None,
    risk_level: Optional[str] = None,
    device: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: OptimizationService = Depends(get_optimization_service),
) -> RecommendationListResponse:
    return await service.list_recommendations(
        q=q, risk_level=risk_level, device=device, limit=limit, offset=offset
    )


@router.get("/recommendations/{rec_id}", response_model=OptimizationRecommendation)
async def get_recommendation(
    rec_id: str,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationRecommendation:
    item = await service.get(rec_id)
    if not item:
        raise HTTPException(404, "Recommendation not found")
    return item


@router.delete("/recommendations/{rec_id}")
async def delete_recommendation(
    rec_id: str,
    service: OptimizationService = Depends(get_optimization_service),
) -> dict:
    ok = await service.delete(rec_id)
    if not ok:
        raise HTTPException(404, "Recommendation not found")
    return {"deleted": rec_id}


@router.post("/recommendations/compare", response_model=list[OptimizationRecommendation])
async def compare_recommendations(
    body: CompareRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> list[OptimizationRecommendation]:
    return await service.compare(body.ids)


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    service: OptimizationService = Depends(get_optimization_service),
) -> AnalyticsSummary:
    return await service.analytics()


@router.post("/upload", response_model=OptimizationRecommendation)
async def upload_dataset(
    file: UploadFile = File(...),
    persist: bool = True,
    service: OptimizationService = Depends(get_optimization_service),
    settings: Settings = Depends(get_settings),
) -> OptimizationRecommendation:
    """Upload OptimizationContext JSON and generate a recommendation."""
    raw = await file.read()
    upload_dir = Path(settings.data_dir) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / f"{uuid4()}_{file.filename or 'dataset.json'}"
    dest.write_bytes(raw)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Invalid JSON: {exc}") from exc

    if "context" in payload:
        ctx = OptimizationContext.model_validate(payload["context"])
    else:
        ctx = OptimizationContext.model_validate(payload)
    return await service.optimize(ctx, persist=persist)
