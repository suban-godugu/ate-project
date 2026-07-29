"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from backend.core.config import Settings, get_settings
from backend.services.coverage_service import CoverageService, get_coverage_service
from backend.services.data_loader import DataLoader, get_data_loader
from backend.services.dataset_service import DatasetService, get_dataset_service
from backend.services.failure_service import FailureService, get_failure_service
from backend.services.gap_analysis_service import (
    GapAnalysisService,
    get_gap_analysis_service,
)
from backend.services.low_power_service import LowPowerService, get_low_power_service
from backend.services.ordering_service import OrderingService, get_ordering_service
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.services.recommendation_orchestrator import (
    RecommendationOrchestrator,
    get_recommendation_orchestrator,
)
from backend.services.redundancy_service import (
    RedundancyService,
    get_redundancy_service,
)
from backend.services.removal_service import RemovalService, get_removal_service


def _resolve_dataset_service(request: Request) -> DatasetService:
    service = getattr(request.app.state, "dataset_service", None)
    if isinstance(service, DatasetService):
        return service
    return get_dataset_service(get_settings())


def _resolve_data_loader(request: Request) -> DataLoader:
    loader = getattr(request.app.state, "data_loader", None)
    if isinstance(loader, DataLoader):
        return loader
    return get_data_loader(
        get_settings(),
        _resolve_dataset_service(request),
    )


def _resolve_pattern_feature_builder(request: Request) -> PatternFeatureBuilder:
    builder = getattr(request.app.state, "pattern_feature_builder", None)
    if isinstance(builder, PatternFeatureBuilder):
        return builder
    return get_pattern_feature_builder(_resolve_data_loader(request))


def _resolve_redundancy_service(request: Request) -> RedundancyService:
    service = getattr(request.app.state, "redundancy_service", None)
    if isinstance(service, RedundancyService):
        return service
    return get_redundancy_service(
        _resolve_data_loader(request),
        _resolve_pattern_feature_builder(request),
    )


def _resolve_removal_service(request: Request) -> RemovalService:
    service = getattr(request.app.state, "removal_service", None)
    if isinstance(service, RemovalService):
        return service
    return get_removal_service(
        get_settings(),
        _resolve_data_loader(request),
        _resolve_pattern_feature_builder(request),
        _resolve_redundancy_service(request),
    )


def _resolve_ordering_service(request: Request) -> OrderingService:
    service = getattr(request.app.state, "ordering_service", None)
    if isinstance(service, OrderingService):
        return service
    return get_ordering_service(
        get_settings(),
        _resolve_data_loader(request),
        _resolve_pattern_feature_builder(request),
    )


def _resolve_gap_analysis_service(request: Request) -> GapAnalysisService:
    service = getattr(request.app.state, "gap_analysis_service", None)
    if isinstance(service, GapAnalysisService):
        return service
    return get_gap_analysis_service(
        get_settings(),
        _resolve_data_loader(request),
        _resolve_pattern_feature_builder(request),
        _resolve_ordering_service(request),
    )


def _resolve_low_power_service(request: Request) -> LowPowerService:
    service = getattr(request.app.state, "low_power_service", None)
    if isinstance(service, LowPowerService):
        return service
    return get_low_power_service(
        get_settings(),
        _resolve_pattern_feature_builder(request),
        _resolve_redundancy_service(request),
        _resolve_removal_service(request),
    )


def _resolve_coverage_service(request: Request) -> CoverageService:
    service = getattr(request.app.state, "coverage_service", None)
    if isinstance(service, CoverageService):
        return service
    return get_coverage_service(
        get_settings(),
        _resolve_pattern_feature_builder(request),
        _resolve_ordering_service(request),
        _resolve_gap_analysis_service(request),
    )


def _resolve_recommendation_orchestrator(
    request: Request,
) -> RecommendationOrchestrator:
    service = getattr(request.app.state, "recommendation_orchestrator", None)
    if isinstance(service, RecommendationOrchestrator):
        return service
    return get_recommendation_orchestrator(
        get_settings(),
        _resolve_pattern_feature_builder(request),
        _resolve_redundancy_service(request),
        _resolve_removal_service(request),
        _resolve_ordering_service(request),
        _resolve_gap_analysis_service(request),
        _resolve_low_power_service(request),
        _resolve_coverage_service(request),
    )


def _resolve_failure_service(request: Request) -> FailureService:
    service = getattr(request.app.state, "failure_service", None)
    if isinstance(service, FailureService):
        return service
    return get_failure_service(_resolve_data_loader(request))


SettingsDependency = Annotated[Settings, Depends(get_settings)]
DatasetServiceDependency = Annotated[
    DatasetService, Depends(_resolve_dataset_service)
]
DataLoaderDependency = Annotated[DataLoader, Depends(_resolve_data_loader)]
PatternFeatureBuilderDependency = Annotated[
    PatternFeatureBuilder, Depends(_resolve_pattern_feature_builder)
]
RedundancyServiceDependency = Annotated[
    RedundancyService, Depends(_resolve_redundancy_service)
]
RemovalServiceDependency = Annotated[
    RemovalService, Depends(_resolve_removal_service)
]
OrderingServiceDependency = Annotated[
    OrderingService, Depends(_resolve_ordering_service)
]
GapAnalysisServiceDependency = Annotated[
    GapAnalysisService, Depends(_resolve_gap_analysis_service)
]
LowPowerServiceDependency = Annotated[
    LowPowerService, Depends(_resolve_low_power_service)
]
CoverageServiceDependency = Annotated[
    CoverageService, Depends(_resolve_coverage_service)
]
RecommendationOrchestratorDependency = Annotated[
    RecommendationOrchestrator, Depends(_resolve_recommendation_orchestrator)
]
FailureServiceDependency = Annotated[
    FailureService, Depends(_resolve_failure_service)
]
