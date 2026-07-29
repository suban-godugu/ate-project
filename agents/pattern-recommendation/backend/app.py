"""FastAPI application factory and entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.router import api_router
from backend.core.config import Settings, get_settings
from backend.core.exceptions import register_exception_handlers
from backend.core.logging import configure_logging, get_logger
from backend.services.data_loader import get_data_loader, reset_data_loader
from backend.services.dataset_service import (
    get_dataset_service,
    reset_dataset_service,
)
from backend.services.coverage_service import (
    get_coverage_service,
    reset_coverage_service,
)
from backend.services.failure_service import (
    get_failure_service,
    reset_failure_service,
)
from backend.services.gap_analysis_service import (
    get_gap_analysis_service,
    reset_gap_analysis_service,
)
from backend.services.low_power_service import (
    get_low_power_service,
    reset_low_power_service,
)
from backend.services.ml_feedback_store import (
    get_ml_feedback_store,
    reset_ml_feedback_store,
)
from backend.services.ml_scoring_service import (
    get_ml_scoring_service,
    reset_ml_scoring_service,
)
from backend.services.ordering_service import (
    get_ordering_service,
    reset_ordering_service,
)
from backend.services.pattern_feature_builder import (
    get_pattern_feature_builder,
    reset_pattern_feature_builder,
)
from backend.services.recommendation_orchestrator import (
    get_recommendation_orchestrator,
    reset_recommendation_orchestrator,
)
from backend.services.redundancy_service import (
    get_redundancy_service,
    reset_redundancy_service,
)
from backend.services.removal_service import (
    get_removal_service,
    reset_removal_service,
)
from backend.utils.request_logging import RequestLoggingMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure an isolated FastAPI application instance."""
    app_settings = settings or get_settings()
    configure_logging(app_settings)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        logger = get_logger()
        logger.info(
            "Application startup project=%s version=%s",
            app_settings.project_name,
            app_settings.version,
        )
        reset_dataset_service()
        reset_data_loader()
        reset_pattern_feature_builder()
        reset_redundancy_service()
        reset_removal_service()
        reset_ordering_service()
        reset_gap_analysis_service()
        reset_low_power_service()
        reset_coverage_service()
        reset_recommendation_orchestrator()
        reset_failure_service()
        reset_ml_scoring_service()
        reset_ml_feedback_store()

        dataset_service = get_dataset_service(app_settings)
        dataset_service.discover()
        data_loader = get_data_loader(app_settings, dataset_service)
        pattern_builder = get_pattern_feature_builder(data_loader)
        ml_scoring_service = get_ml_scoring_service(app_settings)
        ml_feedback_store = get_ml_feedback_store(app_settings)
        redundancy_service = get_redundancy_service(data_loader, pattern_builder)
        removal_service = get_removal_service(
            app_settings,
            data_loader,
            pattern_builder,
            redundancy_service,
            ml_scoring_service,
        )
        ordering_service = get_ordering_service(
            app_settings,
            data_loader,
            pattern_builder,
            ml_scoring_service,
        )
        gap_analysis_service = get_gap_analysis_service(
            app_settings,
            data_loader,
            pattern_builder,
            ordering_service,
        )
        low_power_service = get_low_power_service(
            app_settings,
            pattern_builder,
            redundancy_service,
            removal_service,
        )
        coverage_service = get_coverage_service(
            app_settings,
            pattern_builder,
            ordering_service,
            gap_analysis_service,
        )
        recommendation_orchestrator = get_recommendation_orchestrator(
            app_settings,
            pattern_builder,
            redundancy_service,
            removal_service,
            ordering_service,
            gap_analysis_service,
            low_power_service,
            coverage_service,
        )
        failure_service = get_failure_service(data_loader)

        application.state.dataset_service = dataset_service
        application.state.data_loader = data_loader
        application.state.pattern_feature_builder = pattern_builder
        application.state.redundancy_service = redundancy_service
        application.state.removal_service = removal_service
        application.state.ordering_service = ordering_service
        application.state.gap_analysis_service = gap_analysis_service
        application.state.low_power_service = low_power_service
        application.state.coverage_service = coverage_service
        application.state.recommendation_orchestrator = recommendation_orchestrator
        application.state.failure_service = failure_service
        application.state.ml_scoring_service = ml_scoring_service
        application.state.ml_feedback_store = ml_feedback_store
        # Heavy analyses are built lazily on first API request.
        yield
        logger.info("Application shutdown project=%s", app_settings.project_name)

    application = FastAPI(
        title=app_settings.project_name,
        description=app_settings.description,
        version=app_settings.version,
        docs_url=app_settings.docs_url,
        redoc_url=app_settings.redoc_url,
        openapi_url=app_settings.openapi_url,
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    application.add_middleware(RequestLoggingMiddleware)
    application.include_router(api_router, prefix=app_settings.api_prefix)
    register_exception_handlers(application)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    runtime_settings = get_settings()
    uvicorn.run(
        "backend.app:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        log_level=runtime_settings.log_level.lower(),
        reload=False,
    )
