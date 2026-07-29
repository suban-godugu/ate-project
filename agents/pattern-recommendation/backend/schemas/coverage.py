"""Coverage improvement recommendation schemas (toggle/fail proxy only)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CoverageReasonCode = Literal[
    "LOW_TOGGLE_COVERAGE",
    "UNDER_TESTED_CHAIN",
    "LATE_HIGH_SEVERITY_PATTERN",
    "HIGH_FAILURE_DENSITY",
    "GAP_ANALYSIS_MATCH",
]

CoverageRecommendationType = Literal[
    "IMPROVE_TOGGLE",
    "TARGET_CHAIN",
    "REORDER",
    "GAP_REQUEST",
]


class CoverageRecommendation(BaseModel):
    """One coverage-proxy recommendation — never claims ATPG fault coverage."""

    pattern_id: str = ""
    recommendation_type: CoverageRecommendationType
    reason_codes: list[CoverageReasonCode] = Field(default_factory=list)
    affected_chains: list[str] = Field(default_factory=list)
    affected_lots: list[str] = Field(default_factory=list)
    priority: float = 0.0


class CoverageRecommendationList(BaseModel):
    """All coverage-proxy recommendations with an explicit disclaimer."""

    coverage_type: Literal["toggle_and_fail_proxy"] = "toggle_and_fail_proxy"
    recommendations: list[CoverageRecommendation] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None


class CoverageStatistics(BaseModel):
    """Aggregate coverage-proxy statistics."""

    coverage_type: Literal["toggle_and_fail_proxy"] = "toggle_and_fail_proxy"
    patterns_flagged: int = 0
    chains_flagged: int = 0
    reorder_recommendations: int = 0
    gap_matches: int = 0
    average_priority: float = 0.0


class CoverageRefreshResponse(BaseModel):
    """Refresh acknowledgement carrying the proxy disclaimer."""

    success: bool = True
    message: str
    coverage_type: Literal["toggle_and_fail_proxy"] = "toggle_and_fail_proxy"
    data: CoverageStatistics
