"""Failure aggregation API schemas for dashboard consumption."""

from typing import Any, Literal

from pydantic import BaseModel, Field

SeverityLabel = Literal["HIGH", "MEDIUM", "LOW"]


class FailureSummaryStats(BaseModel):
    """Aggregate failure-health KPIs from the aggregation agent."""

    total_logs: int = 0
    failed_logs: int = 0
    good_logs: int = 0
    unique_patterns: int = 0
    total_pattern_occurrences: int = 0
    total_lots: int = 0
    severity_high: int = 0
    severity_medium: int = 0
    severity_low: int = 0


class FailurePatternRow(BaseModel):
    """One ranked failing-pattern row for the dashboard grid."""

    rank: int = 0
    pattern_id: str = ""
    failed_logs: int = 0
    coverage_percent: float = 0.0
    severity: SeverityLabel | str = "LOW"
    affected_lots: list[str] = Field(default_factory=list)
    failing_logs: list[str] = Field(default_factory=list)
    failing_log_count: int = 0


class FailureSummaryResponse(BaseModel):
    """Full failure aggregation payload for the dashboard."""

    success: bool = True
    message: str = "Failure summary ready"
    summary: FailureSummaryStats = Field(default_factory=FailureSummaryStats)
    patterns: list[FailurePatternRow] = Field(default_factory=list)
    total_patterns: int = 0


class FailureDashboardRowsResponse(BaseModel):
    """Grid-oriented rows matching outputs/dashboard_data.json shape."""

    success: bool = True
    message: str = "Failure dashboard rows ready"
    rows: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
