"""Pattern removal recommendation schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RemovalReasonCode = Literal[
    "REDUNDANT_NEAR_DUP",
    "LOW_UNIQUE_DETECTION",
    "LOW_TOGGLE_ACTIVITY",
]


class RemovalRecommendation(BaseModel):
    """Deterministic removal recommendation for one redundant pattern."""

    pattern_id: str
    cluster_id: str
    representative_pattern: str
    removal_priority: float
    confidence: float
    unique_fail_contribution: float
    normalized_unique_fail_contribution: float = 0.0
    normalized_toggle_coverage: float = 0.0
    reason_codes: list[RemovalReasonCode] = Field(default_factory=list)


class RemovalRecommendationList(BaseModel):
    """Ranked removal recommendations."""

    recommendations: list[RemovalRecommendation] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None


class RemovalStatistics(BaseModel):
    """Aggregate removal recommendation statistics."""

    candidates: int = 0
    recommended: int = 0
    average_priority: float = 0.0
    highest_priority: float = 0.0


class RemovalRefreshResponse(BaseModel):
    """Refresh acknowledgement for removal recommendations."""

    success: bool = True
    message: str
    data: RemovalStatistics
