"""Pattern feature schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SeverityValue = Literal["HIGH", "MEDIUM", "LOW", "NONE"]


class PatternFeature(BaseModel):
    """Canonical per-pattern metrics shared by all recommendation services."""

    pattern_id: str
    total_executions: int = 0
    fail_executions: int = 0
    fail_rate: float = 0.0
    mean_toggle_coverage: float = 0.0
    mean_toggle_density: float = 0.0
    mean_toggle_count: float = 0.0
    failed_logs: list[str] = Field(default_factory=list)
    failed_chains: list[str] = Field(default_factory=list)
    coverage_percent: float = 0.0
    severity: SeverityValue = "NONE"


class PatternList(BaseModel):
    """Full pattern feature index payload."""

    patterns: list[PatternFeature] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None


class PatternStatistics(BaseModel):
    """Aggregate statistics over the pattern feature index."""

    patterns: int = 0
    total_executions: int = 0
    failed_patterns: int = 0
    average_fail_rate: float = 0.0
    average_toggle_density: float = 0.0


class PatternRefreshResponse(BaseModel):
    """Refresh acknowledgement for the pattern feature cache."""

    success: bool = True
    message: str
    data: PatternList
