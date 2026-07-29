"""Redundancy detection API endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import RedundancyServiceDependency
from backend.schemas.redundancy import (
    ClusterList,
    RedundancyList,
    RedundancyRefreshResponse,
    RedundancyStatistics,
    RedundantPattern,
)

router = APIRouter(prefix="/redundancy", tags=["Redundancy"])


@router.get(
    "/statistics",
    response_model=RedundancyStatistics,
    summary="Redundancy statistics",
)
async def redundancy_statistics(
    service: RedundancyServiceDependency,
) -> RedundancyStatistics:
    return service.get_statistics()


@router.get(
    "/clusters",
    response_model=ClusterList,
    summary="List redundancy clusters",
)
async def list_clusters(
    service: RedundancyServiceDependency,
) -> ClusterList:
    return service.get_clusters()


@router.post(
    "/refresh",
    response_model=RedundancyRefreshResponse,
    summary="Rebuild redundancy analysis",
)
async def refresh_redundancy(
    service: RedundancyServiceDependency,
) -> RedundancyRefreshResponse:
    stats = service.refresh()
    return RedundancyRefreshResponse(
        success=True,
        message="Redundancy analysis rebuilt",
        data=stats,
    )


@router.get(
    "",
    response_model=RedundancyList,
    summary="List redundant patterns",
)
async def list_redundant_patterns(
    service: RedundancyServiceDependency,
) -> RedundancyList:
    return service.get_redundant_patterns()


@router.get(
    "/{pattern_id}",
    response_model=RedundantPattern,
    summary="Get redundancy info for one pattern",
)
async def get_redundant_pattern(
    pattern_id: str,
    service: RedundancyServiceDependency,
) -> RedundantPattern:
    return service.get_pattern(pattern_id)
