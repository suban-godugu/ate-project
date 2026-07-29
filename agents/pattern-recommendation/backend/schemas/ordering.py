"""Pattern ordering recommendation schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.schemas.patterns import SeverityValue

OrderingReasonCode = Literal[
    "HIGH_FAILURE_RATE",
    "HIGH_SEVERITY",
    "HIGH_TOGGLE_COVERAGE",
    "MEDIUM_FAILURE_RATE",
    "LOW_FAILURE_RATE",
]


class OrderedPattern(BaseModel):
    """One pattern in the recommended execution order."""

    pattern_id: str
    execution_rank: int
    order_score: float
    fail_rate: float
    severity: SeverityValue
    mean_toggle_coverage: float
    reason_codes: list[OrderingReasonCode] = Field(default_factory=list)


class OrderingList(BaseModel):
    """Complete ordered pattern list."""

    patterns: list[OrderedPattern] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None


class OrderingStatistics(BaseModel):
    """Aggregate ordering statistics."""

    total_patterns: int = 0
    highest_score: float = 0.0
    lowest_score: float = 0.0
    average_score: float = 0.0
    high_priority_patterns: int = 0


class OrderingRefreshResponse(BaseModel):
    """Refresh acknowledgement for ordering recommendations."""

    success: bool = True
    message: str
    data: OrderingStatistics
