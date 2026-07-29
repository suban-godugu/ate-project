"""Pydantic v2 contracts for production FA-FR-005."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeRecurrenceRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = Field(default=None, max_length=36)
    computation_id: str | None = Field(default=None, max_length=36)
    async_execution: bool = False
    incremental: bool = True
    historical_window: int = Field(default=50, ge=2, le=500)
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_recurring_pattern_ids: list[str] = Field(default_factory=list)
    expected_non_recurring_pattern_ids: list[str] = Field(default_factory=list)
    actor: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def validate_source(self) -> "AnalyzeRecurrenceRequest":
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class RecurrenceSummary(BaseModel):
    recurrence_id: str
    analysis_id: str
    pattern_id: str
    pattern_name: str
    fault_type: str
    recurrence_count: int
    recurrence_frequency: float
    recurrence_percentage: float
    confidence_score: float
    severity: str
    trend_direction: str
    first_occurrence: str
    latest_occurrence: str
    historical_frequency: float
    hotspot_location: dict = Field(default_factory=dict)
    engineering_recommendation: str
    similarity_group: str | None = None
    created_at: str | None = None


class AnalyzeRecurrenceResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = None
    computation_id: str | None = None
    classification_execution_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed"]
    config_version: str = ""
    source_record_count: int = 0
    pattern_count: int = 0
    recurrence_count: int = 0
    hotspot_count: int = 0
    processing_ms: float = 0.0
    recurrences: list[RecurrenceSummary] = Field(default_factory=list)
    benchmark_metrics: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
