"""Pattern ordering recommendation API endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import OrderingServiceDependency
from backend.schemas.ordering import (
    OrderedPattern,
    OrderingList,
    OrderingRefreshResponse,
    OrderingStatistics,
)

router = APIRouter(
    prefix="/recommendations/ordering",
    tags=["Ordering Recommendations"],
)


@router.get(
    "/statistics",
    response_model=OrderingStatistics,
    summary="Ordering recommendation statistics",
)
async def ordering_statistics(
    service: OrderingServiceDependency,
) -> OrderingStatistics:
    return service.get_statistics()


@router.post(
    "/refresh",
    response_model=OrderingRefreshResponse,
    summary="Rebuild ordering recommendations",
)
async def refresh_ordering(
    service: OrderingServiceDependency,
) -> OrderingRefreshResponse:
    stats = service.refresh()
    return OrderingRefreshResponse(
        success=True,
        message="Ordering recommendations rebuilt",
        data=stats,
    )


@router.get(
    "",
    response_model=OrderingList,
    summary="List ordered patterns",
)
async def list_ordered_patterns(
    service: OrderingServiceDependency,
) -> OrderingList:
    return service.get_ordering()


@router.get(
    "/{pattern_id}",
    response_model=OrderedPattern,
    summary="Get ordering for one pattern",
)
async def get_ordered_pattern(
    pattern_id: str,
    service: OrderingServiceDependency,
) -> OrderedPattern:
    return service.get_pattern(pattern_id)
