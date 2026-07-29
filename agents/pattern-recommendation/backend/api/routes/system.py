"""Root and service-status endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import SettingsDependency
from backend.core.constants import STATUS_HEALTHY
from backend.schemas.responses import HealthResponse, RootResponse, VersionResponse

router = APIRouter(tags=["System"])


@router.get("/", response_model=RootResponse, summary="API information")
async def get_root(settings: SettingsDependency) -> RootResponse:
    """Return project identity and API discovery links."""
    return RootResponse(
        project_name=settings.project_name,
        version=settings.version,
        status=settings.status,
        api={
            "openapi": settings.openapi_url,
            "swagger": settings.docs_url,
            "redoc": settings.redoc_url,
            "health": "/health",
            "version": "/version",
            "inputs": "/inputs",
            "inputs_connect": "/inputs/connect",
            "datasets": "/datasets",
            "datasets_status": "/datasets/status",
            "datasets_summary": "/datasets/summary",
            "datasets_refresh": "/datasets/refresh",
            "patterns": "/patterns",
            "patterns_statistics": "/patterns/statistics",
            "patterns_refresh": "/patterns/refresh",
            "redundancy": "/redundancy",
            "redundancy_clusters": "/redundancy/clusters",
            "redundancy_statistics": "/redundancy/statistics",
            "redundancy_refresh": "/redundancy/refresh",
            "removal_recommendations": "/recommendations/removal",
            "removal_statistics": "/recommendations/removal/statistics",
            "removal_refresh": "/recommendations/removal/refresh",
            "ordering_recommendations": "/recommendations/ordering",
            "ordering_statistics": "/recommendations/ordering/statistics",
            "ordering_refresh": "/recommendations/ordering/refresh",
            "gap_analysis": "/recommendations/gap-analysis",
            "gap_analysis_statistics": "/recommendations/gap-analysis/statistics",
            "gap_analysis_refresh": "/recommendations/gap-analysis/refresh",
            "low_power_proxy": "/recommendations/low-power",
            "low_power_statistics": "/recommendations/low-power/statistics",
            "low_power_refresh": "/recommendations/low-power/refresh",
            "coverage_proxy": "/recommendations/coverage",
            "coverage_statistics": "/recommendations/coverage/statistics",
            "coverage_refresh": "/recommendations/coverage/refresh",
            "unified_recommendations": "/recommendations",
            "unified_summary": "/recommendations/summary",
            "unified_dashboard": "/recommendations/dashboard",
            "unified_refresh": "/recommendations/refresh",
            "failures_summary": "/failures/summary",
            "failures_dashboard_rows": "/failures/dashboard-rows",
            "failures_refresh": "/failures/refresh",
            "ml_status": "/ml/status",
            "ml_feedback": "/ml/feedback",
            "ml_feedback_recent": "/ml/feedback/recent",
        },
    )


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def get_health() -> HealthResponse:
    """Return process health."""
    return HealthResponse(status=STATUS_HEALTHY)


@router.get("/version", response_model=VersionResponse, summary="API version")
async def get_version(settings: SettingsDependency) -> VersionResponse:
    """Return the configured application version."""
    return VersionResponse(version=settings.version)
