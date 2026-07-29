"""Low-activity recommendation schemas using a toggle-activity proxy."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ToggleMetric = Literal["toggle_density", "toggle_count"]
LowPowerReasonCode = Literal[
    "LOW_ACTIVITY",
    "FAILURE_COVERAGE_PRESERVED",
    "REQUIRED_FAILED_REPRESENTATIVE",
]


class LowPowerPattern(BaseModel):
    """One selected pattern in the toggle-activity proxy set."""

    pattern_id: str
    activity_score: float
    toggle_metric: ToggleMetric
    selected: bool = True
    representative: bool = False
    coverage_retained: bool = False
    reason_codes: list[LowPowerReasonCode] = Field(default_factory=list)
    power_proxy: ToggleMetric


class LowPowerPatternSet(BaseModel):
    """Recommended low-activity set with an explicit proxy disclaimer."""

    power_proxy: bool = True
    proxy_metric: ToggleMetric
    patterns: list[LowPowerPattern] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None


class LowPowerStatistics(BaseModel):
    """Statistics for the toggle-activity proxy analysis."""

    power_proxy: bool = True
    proxy_metric: ToggleMetric
    patterns_analyzed: int = 0
    selected_patterns: int = 0
    coverage_retention: float = 0.0
    average_activity: float = 0.0
    threshold_percentile: float = 0.0


class LowPowerRefreshResponse(BaseModel):
    """Refresh acknowledgement carrying the proxy disclaimer."""

    success: bool = True
    message: str
    power_proxy: bool = True
    proxy_metric: ToggleMetric
    data: LowPowerStatistics
