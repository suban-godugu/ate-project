"""ATPG gap-analysis request API endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import GapAnalysisServiceDependency
from backend.schemas.gap_analysis import (
    GapAnalysisList,
    GapAnalysisRefreshResponse,
    GapAnalysisStatistics,
)

router = APIRouter(
    prefix="/recommendations/gap-analysis",
    tags=["Gap Analysis"],
)


@router.get(
    "/statistics",
    response_model=GapAnalysisStatistics,
    summary="Gap analysis statistics",
)
async def gap_analysis_statistics(
    service: GapAnalysisServiceDependency,
) -> GapAnalysisStatistics:
    return service.get_statistics()


@router.post(
    "/refresh",
    response_model=GapAnalysisRefreshResponse,
    summary="Rebuild gap analysis requests",
)
async def refresh_gap_analysis(
    service: GapAnalysisServiceDependency,
) -> GapAnalysisRefreshResponse:
    stats = service.refresh()
    return GapAnalysisRefreshResponse(
        success=True,
        message="Gap analysis rebuilt",
        data=stats,
    )


@router.get(
    "",
    response_model=GapAnalysisList,
    summary="List ATPG gap requests",
)
async def list_gap_requests(
    service: GapAnalysisServiceDependency,
) -> GapAnalysisList:
    return service.get_requests()
