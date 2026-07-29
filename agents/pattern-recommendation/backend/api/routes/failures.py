"""Failure aggregation API endpoints for the dashboard."""

from fastapi import APIRouter

from backend.api.dependencies import FailureServiceDependency
from backend.schemas.failures import (
    FailureDashboardRowsResponse,
    FailureSummaryResponse,
)

router = APIRouter(prefix="/failures", tags=["Failure Aggregation"])


@router.get(
    "/summary",
    response_model=FailureSummaryResponse,
    summary="Failure aggregation summary and ranked patterns",
)
async def get_failure_summary(
    service: FailureServiceDependency,
) -> FailureSummaryResponse:
    """Return KPIs and ranked failing patterns from failure_summary.json."""
    return service.get_summary()


@router.get(
    "/dashboard-rows",
    response_model=FailureDashboardRowsResponse,
    summary="Failure aggregation grid rows",
)
async def get_failure_dashboard_rows(
    service: FailureServiceDependency,
) -> FailureDashboardRowsResponse:
    """Return grid-oriented rows for Streamlit/React data tables."""
    return service.get_dashboard_rows()


@router.post(
    "/refresh",
    response_model=FailureSummaryResponse,
    summary="Reload failure_summary.json from disk",
)
async def refresh_failure_summary(
    service: FailureServiceDependency,
) -> FailureSummaryResponse:
    """Invalidate the failure_summary cache and rebuild the payload."""
    return service.refresh()
