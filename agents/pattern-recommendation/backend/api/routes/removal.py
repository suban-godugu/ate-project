"""Pattern removal recommendation API endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import RemovalServiceDependency
from backend.schemas.removal import (
    RemovalRecommendation,
    RemovalRecommendationList,
    RemovalRefreshResponse,
    RemovalStatistics,
)

router = APIRouter(
    prefix="/recommendations/removal",
    tags=["Removal Recommendations"],
)


@router.get(
    "/statistics",
    response_model=RemovalStatistics,
    summary="Removal recommendation statistics",
)
async def removal_statistics(
    service: RemovalServiceDependency,
) -> RemovalStatistics:
    return service.get_statistics()


@router.post(
    "/refresh",
    response_model=RemovalRefreshResponse,
    summary="Rebuild removal recommendations",
)
async def refresh_removal(
    service: RemovalServiceDependency,
) -> RemovalRefreshResponse:
    stats = service.refresh()
    return RemovalRefreshResponse(
        success=True,
        message="Removal recommendations rebuilt",
        data=stats,
    )


@router.get(
    "",
    response_model=RemovalRecommendationList,
    summary="List ranked removal recommendations",
)
async def list_removal_recommendations(
    service: RemovalServiceDependency,
) -> RemovalRecommendationList:
    return service.get_recommendations()


@router.get(
    "/{pattern_id}",
    response_model=RemovalRecommendation,
    summary="Get removal recommendation for one pattern",
)
async def get_removal_recommendation(
    pattern_id: str,
    service: RemovalServiceDependency,
) -> RemovalRecommendation:
    return service.get_recommendation(pattern_id)
