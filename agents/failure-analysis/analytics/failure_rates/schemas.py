"""Pydantic v2 contracts for production FA-FR-003 APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

AGGREGATION_LEVELS = {
    "pattern",
    "device",
    "die",
    "wafer",
    "lot",
    "test_program",
    "batch",
}


class ComputeFailureRatesRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = None
    async_execution: bool = False
    aggregation_levels: list[str] = Field(
        default_factory=lambda: sorted(AGGREGATION_LEVELS)
    )
    window_size: int = Field(default=5, ge=1, le=100)
    actor: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_source_and_levels(self) -> "ComputeFailureRatesRequest":
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        invalid = set(self.aggregation_levels) - AGGREGATION_LEVELS
        if invalid:
            raise ValueError(f"Unsupported aggregation levels: {sorted(invalid)}")
        if not self.aggregation_levels:
            raise ValueError("At least one aggregation level is required")
        return self


class FailureRateSummary(BaseModel):
    id: str
    computation_id: str
    pattern_id: str
    aggregation_level: str
    aggregation_key: str
    total_tests: int
    pass_count: int
    fail_count: int
    failure_percentage: float
    failure_density: float
    pattern_frequency: float
    moving_average: float | None = None
    baseline_percentage: float | None = None
    historical_delta: float | None = None
    trend_status: str
    threshold_status: str
    severity_level: str
    computed_at: str | None = None


class ComputeFailureRatesResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    formula_version: str = ""
    source_record_count: int = 0
    pattern_count: int = 0
    metric_count: int = 0
    processing_ms: float = 0.0
    metrics: list[FailureRateSummary] = Field(default_factory=list)
    benchmark_metrics: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ThresholdRequest(BaseModel):
    configuration_key: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    pattern_id: str | None = Field(default=None, max_length=128)
    aggregation_level: str | None = None
    warning_percentage: float = Field(ge=0.0, le=100.0)
    critical_percentage: float = Field(ge=0.0, le=100.0)
    abnormal_delta_percentage: float = Field(ge=0.0, le=100.0)
    created_by: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "ThresholdRequest":
        if self.warning_percentage > self.critical_percentage:
            raise ValueError("warning_percentage cannot exceed critical_percentage")
        if self.aggregation_level and self.aggregation_level not in AGGREGATION_LEVELS:
            raise ValueError("Unsupported aggregation_level")
        return self
