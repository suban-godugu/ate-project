"""Dependency injection providers."""

from __future__ import annotations

from functools import lru_cache

from .config import Settings, get_settings
from ..infrastructure.llm.client import LLMClient
from ..infrastructure.repositories.recommendation_repository import RecommendationRepository
from ..services.optimization_service import OptimizationService


@lru_cache
def get_recommendation_repository() -> RecommendationRepository:
    return RecommendationRepository(get_settings().data_dir / "recommendations")


@lru_cache
def get_llm_client() -> LLMClient:
    return LLMClient(get_settings())


def get_optimization_service() -> OptimizationService:
    return OptimizationService(
        settings=get_settings(),
        llm=get_llm_client(),
        repository=get_recommendation_repository(),
    )


def get_app_settings() -> Settings:
    return get_settings()
