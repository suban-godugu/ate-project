"""Toggle-activity proxy recommendation endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import LowPowerServiceDependency
from backend.schemas.low_power import (
    LowPowerPatternSet,
    LowPowerRefreshResponse,
    LowPowerStatistics,
)

router = APIRouter(
    prefix="/recommendations/low-power",
    tags=["Low-Activity Proxy Recommendations"],
)


@router.get(
    "/statistics",
    response_model=LowPowerStatistics,
    summary="Low-activity proxy statistics",
)
async def low_power_statistics(
    service: LowPowerServiceDependency,
) -> LowPowerStatistics:
    """Return statistics explicitly labeled as toggle-activity proxy data."""
    return service.get_statistics()


@router.post(
    "/refresh",
    response_model=LowPowerRefreshResponse,
    summary="Rebuild low-activity proxy recommendations",
)
async def refresh_low_power(
    service: LowPowerServiceDependency,
) -> LowPowerRefreshResponse:
    """Explicitly rebuild the cached low-activity pattern set."""
    statistics = service.refresh()
    return LowPowerRefreshResponse(
        success=True,
        message="Toggle-activity proxy recommendations rebuilt",
        power_proxy=True,
        proxy_metric=statistics.proxy_metric,
        data=statistics,
    )


@router.get(
    "",
    response_model=LowPowerPatternSet,
    summary="List selected low-activity patterns",
)
async def list_low_power_patterns(
    service: LowPowerServiceDependency,
) -> LowPowerPatternSet:
    """Return the selected set without making actual-power claims."""
    return service.get_pattern_set()
