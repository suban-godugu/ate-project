"""Unified recommendation schemas for dashboard consumption."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RecommendationFeasibility(BaseModel):
    """Stable feasibility contract for the frontend."""

    redundant_patterns: Literal["full"] = "full"
    pattern_removal: Literal["full"] = "full"
    pattern_ordering: Literal["full"] = "full"
    additional_atpg: Literal["gap_requests_only"] = "gap_requests_only"
    low_power_sets: Literal["toggle_activity_proxy"] = "toggle_activity_proxy"
    coverage_improvement: Literal["toggle_fail_proxy"] = "toggle_fail_proxy"


class UnifiedRecommendationSummary(BaseModel):
    """Aggregate counts across all recommendation services."""

    patterns_analyzed: int = 0
    clusters: int = 0
    removal_candidates: int = 0
    ordering_candidates: int = 0
    gap_requests: int = 0
    low_power_patterns: int = 0
    coverage_recommendations: int = 0


class UnifiedRecommendationBundle(BaseModel):
    """
    Stable frontend contract.

    Do not change field names — this is the dashboard schema.
    """

    summary: UnifiedRecommendationSummary
    feasibility: RecommendationFeasibility = Field(
        default_factory=RecommendationFeasibility
    )
    redundant_patterns: list[dict[str, Any]] = Field(default_factory=list)
    removal_recommendations: list[dict[str, Any]] = Field(default_factory=list)
    ordered_patterns: list[dict[str, Any]] = Field(default_factory=list)
    additional_pattern_requests: list[dict[str, Any]] = Field(default_factory=list)
    low_activity_pattern_set: list[dict[str, Any]] = Field(default_factory=list)
    coverage_gap_recommendations: list[dict[str, Any]] = Field(default_factory=list)


class OrchestratorArtifacts(BaseModel):
    """Paths of generated dashboard artifacts."""

    json_path: str = ""
    csv_path: str = ""
    markdown_path: str = ""


class OrchestratorResponse(BaseModel):
    """Unified API payload for the dashboard."""

    success: bool = True
    message: str = "Unified recommendations ready"
    built_at: datetime | None = None
    recommendations: UnifiedRecommendationBundle
    artifacts: OrchestratorArtifacts = Field(default_factory=OrchestratorArtifacts)


class OrchestratorRefreshResponse(BaseModel):
    """Refresh acknowledgement for the orchestrator."""

    success: bool = True
    message: str
    data: OrchestratorResponse
