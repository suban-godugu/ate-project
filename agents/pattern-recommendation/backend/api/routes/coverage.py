"""Coverage improvement proxy recommendation endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import CoverageServiceDependency
from backend.schemas.coverage import (
    CoverageRecommendationList,
    CoverageRefreshResponse,
    CoverageStatistics,
)

router = APIRouter(
    prefix="/recommendations/coverage",
    tags=["Coverage Proxy Recommendations"],
)


@router.get(
    "/statistics",
    response_model=CoverageStatistics,
    summary="Coverage proxy statistics",
)
async def coverage_statistics(
    service: CoverageServiceDependency,
) -> CoverageStatistics:
    return service.get_statistics()


@router.post(
    "/refresh",
    response_model=CoverageRefreshResponse,
    summary="Rebuild coverage proxy recommendations",
)
async def refresh_coverage(
    service: CoverageServiceDependency,
) -> CoverageRefreshResponse:
    stats = service.refresh()
    return CoverageRefreshResponse(
        success=True,
        message="Coverage proxy recommendations rebuilt",
        coverage_type="toggle_and_fail_proxy",
        data=stats,
    )


@router.get(
    "",
    response_model=CoverageRecommendationList,
    summary="List coverage proxy recommendations",
)
async def list_coverage_recommendations(
    service: CoverageServiceDependency,
) -> CoverageRecommendationList:
    return service.get_recommendations()
