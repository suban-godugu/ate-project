"""Unified recommendation orchestrator API for the dashboard."""

from typing import Any

from fastapi import APIRouter

from backend.api.dependencies import RecommendationOrchestratorDependency
from backend.schemas.orchestrator import (
    OrchestratorRefreshResponse,
    OrchestratorResponse,
    UnifiedRecommendationSummary,
)

router = APIRouter(prefix="/recommendations", tags=["Unified Recommendations"])


@router.get(
    "",
    response_model=OrchestratorResponse,
    summary="Unified recommendations for the dashboard",
)
async def get_unified_recommendations(
    service: RecommendationOrchestratorDependency,
) -> OrchestratorResponse:
    """Return every recommendation domain in one stable contract."""
    return service.ensure_built()


@router.get(
    "/summary",
    response_model=UnifiedRecommendationSummary,
    summary="Unified recommendation summary counts",
)
async def get_unified_summary(
    service: RecommendationOrchestratorDependency,
) -> UnifiedRecommendationSummary:
    return service.get_summary()


@router.get(
    "/dashboard",
    summary="Dashboard-ready unified tables",
)
async def get_dashboard_payload(
    service: RecommendationOrchestratorDependency,
) -> dict[str, Any]:
    """Return summary + table sections ready for Streamlit/React grids."""
    return service.get_dashboard()


@router.post(
    "/refresh",
    response_model=OrchestratorRefreshResponse,
    summary="Refresh all recommendation services and regenerate artifacts",
)
async def refresh_unified_recommendations(
    service: RecommendationOrchestratorDependency,
) -> OrchestratorRefreshResponse:
    payload = service.refresh()
    return OrchestratorRefreshResponse(
        success=True,
        message="Unified recommendations refreshed",
        data=payload,
    )
