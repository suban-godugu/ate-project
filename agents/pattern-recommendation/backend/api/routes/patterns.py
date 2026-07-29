"""Pattern feature API endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import PatternFeatureBuilderDependency
from backend.schemas.patterns import (
    PatternFeature,
    PatternList,
    PatternRefreshResponse,
    PatternStatistics,
)

router = APIRouter(prefix="/patterns", tags=["Patterns"])


@router.get(
    "/statistics",
    response_model=PatternStatistics,
    summary="Pattern feature statistics",
)
async def pattern_statistics(
    builder: PatternFeatureBuilderDependency,
) -> PatternStatistics:
    """Return aggregate statistics over the pattern feature index."""
    return builder.get_statistics()


@router.post(
    "/refresh",
    response_model=PatternRefreshResponse,
    summary="Rebuild pattern feature index",
)
async def refresh_patterns(
    builder: PatternFeatureBuilderDependency,
) -> PatternRefreshResponse:
    """Clear dataset caches and rebuild the canonical pattern index."""
    payload = builder.refresh()
    return PatternRefreshResponse(
        success=True,
        message="Pattern feature index rebuilt",
        data=payload,
    )


@router.get(
    "",
    response_model=PatternList,
    summary="List all pattern features",
)
async def list_patterns(
    builder: PatternFeatureBuilderDependency,
) -> PatternList:
    """Return every pattern feature from the canonical index."""
    return builder.ensure_built()


@router.get(
    "/{pattern_id}",
    response_model=PatternFeature,
    summary="Get one pattern feature",
)
async def get_pattern(
    pattern_id: str,
    builder: PatternFeatureBuilderDependency,
) -> PatternFeature:
    """Return a single pattern feature by ID."""
    return builder.get_pattern(pattern_id)
