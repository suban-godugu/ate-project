"""Pydantic v2 contracts for production FA-FR-006."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeCorrelationRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = Field(default=None, max_length=36)
    computation_id: str | None = Field(default=None, max_length=36)
    recurrence_analysis_id: str | None = Field(default=None, max_length=36)
    coefficient_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    significance_level: float | None = Field(default=None, gt=0.0, le=1.0)
    historical_window: int = Field(default=50, ge=2, le=500)
    incremental: bool = True
    async_execution: bool = False
    expected_correlated_pairs: list[str] = Field(default_factory=list)
    expected_uncorrelated_pairs: list[str] = Field(default_factory=list)
    actor: str | None = Field(default=None, max_length=128)
    top_n: int | None = Field(default=None, ge=1, le=500, deprecated=True)

    @model_validator(mode="after")
    def validate_source(self) -> "AnalyzeCorrelationRequest":
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class CorrelationSummary(BaseModel):
    correlation_id: str
    analysis_id: str
    pattern_id: str
    fault_type: str
    correlated_failures: int
    correlation_coefficient: float
    correlation_strength: str
    confidence_score: float
    p_value: float | None = None
    sample_size: int
    severity: str
    trend_status: str
    hotspot_location: dict = Field(default_factory=dict)
    engineering_recommendation: str
    correlation_timestamp: str | None = None


class AnalyzeCorrelationResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed"]
    config_version: str = ""
    upstream_execution_ids: dict = Field(default_factory=dict)
    source_record_count: int = 0
    correlation_count: int = 0
    processing_ms: float = 0.0
    correlations: list[CorrelationSummary] = Field(default_factory=list)
    matrix: dict = Field(default_factory=dict)
    relationship_graph: dict = Field(default_factory=dict)
    benchmark_metrics: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
