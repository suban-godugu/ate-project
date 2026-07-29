"""ATPG gap analysis request schemas (request-only, no vector generation)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

GapRationaleCode = Literal[
    "LOW_TOGGLE_COVERAGE",
    "HIGH_FAILURE_DENSITY",
    "LOW_PATTERN_DIVERSITY",
    "HIGH_PRIORITY_ORDERING",
]

SuggestedFaultModel = Literal["stuck-at", "transition", "Unknown"]


class AdditionalPatternRequest(BaseModel):
    """Structured ATPG pattern request — never claims ATPG execution."""

    request_only: bool = True
    request_id: str = ""
    target_chains: list[str] = Field(default_factory=list)
    target_lots: list[str] = Field(default_factory=list)
    suggested_fault_model: SuggestedFaultModel = "Unknown"
    rationale: list[GapRationaleCode] = Field(default_factory=list)


class GapAnalysisList(BaseModel):
    """All generated ATPG gap requests."""

    requests: list[AdditionalPatternRequest] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None
    gap_percentile: float = 0.0


class GapAnalysisStatistics(BaseModel):
    """Aggregate gap-analysis statistics."""

    requests_generated: int = 0
    chains_flagged: int = 0
    lots_flagged: int = 0
    average_toggle_percentile: float = 0.0


class GapAnalysisRefreshResponse(BaseModel):
    """Refresh acknowledgement for gap analysis."""

    success: bool = True
    message: str
    data: GapAnalysisStatistics
