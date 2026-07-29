"""Pydantic v2 contracts for production FA-FR-009."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PredictFaultRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = Field(default=None, max_length=36)
    computation_id: str | None = Field(default=None, max_length=36)
    recurrence_analysis_id: str | None = Field(default=None, max_length=36)
    correlation_analysis_id: str | None = Field(default=None, max_length=36)
    die_analysis_id: str | None = Field(default=None, max_length=36)
    wafer_analysis_id: str | None = Field(default=None, max_length=36)
    historical_window: int = Field(default=50, ge=2, le=500)
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    minimum_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    model_version: str | None = Field(default=None, max_length=64)
    incremental: bool = True
    async_execution: bool = False
    expected_fault_types: dict[str, str] = Field(
        default_factory=dict,
        description="Optional ground truth map of pattern_id to validated fault type",
    )
    actor: str | None = Field(default=None, max_length=128)
    legacy: bool = Field(
        default=False,
        description="When true, dispatches to the legacy /api/v1/root-cause API.",
    )
    config_path: str | None = None

    @model_validator(mode="after")
    def validate_source(self) -> "PredictFaultRequest":
        if self.legacy:
            if not self.upload_id:
                raise ValueError("legacy mode requires upload_id")
            return self
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class PredictionSummary(BaseModel):
    prediction_id: str
    execution_id: str
    pattern_id: str
    predicted_fault_type: str
    confidence_score: float
    prediction_probability: float
    model_version: str
    predicted_at: str | None = None


class PredictFaultResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed"]
    config_version: str = ""
    model_version: str = ""
    upstream_execution_ids: dict = Field(default_factory=dict)
    source_pattern_count: int = 0
    prediction_count: int = 0
    high_confidence_count: int = 0
    processing_ms: float = 0.0
    predictions: list[PredictionSummary] = Field(default_factory=list)
    statistics: dict = Field(default_factory=dict)
    benchmark_metrics: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Predictions are probable fault types only, not definitive root causes."
    )


class PredictionFeedbackRequest(BaseModel):
    prediction_id: str = Field(max_length=36)
    validated_fault_type: str = Field(max_length=128)
    feedback_status: Literal["confirmed", "rejected", "partial"] = "confirmed"
    engineer_notes: str = Field(default="", max_length=4000)
    learning_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    actor: str | None = Field(default=None, max_length=128)
