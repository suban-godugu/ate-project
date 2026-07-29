"""Pydantic v2 contracts for production FA-FR-007."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeDieRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = Field(default=None, max_length=36)
    computation_id: str | None = Field(default=None, max_length=36)
    recurrence_analysis_id: str | None = Field(default=None, max_length=36)
    correlation_analysis_id: str | None = Field(default=None, max_length=36)
    historical_window: int = Field(default=50, ge=2, le=500)
    hotspot_density_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    cluster_eps: float | None = Field(default=None, gt=0.0, le=100.0)
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    incremental: bool = True
    async_execution: bool = False
    expected_failing_die_ids: list[str] = Field(default_factory=list)
    expected_passing_die_ids: list[str] = Field(default_factory=list)
    actor: str | None = Field(default=None, max_length=128)
    legacy: bool = Field(
        default=False,
        description="When true, dispatches to the legacy /api/v1/die analyzer.",
    )

    @model_validator(mode="after")
    def validate_source(self) -> "AnalyzeDieRequest":
        if self.legacy:
            if not self.upload_id:
                raise ValueError("legacy mode requires upload_id")
            return self
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class DieSummary(BaseModel):
    die_result_id: str
    analysis_id: str
    lot_id: str
    wafer_id: str
    die_id: str
    x: float | None = None
    y: float | None = None
    failure_count: int
    total_tests: int
    failure_density: float
    neighbor_failure_count: int
    is_isolated: bool
    is_failing: bool
    health_score: float
    severity: str
    confidence_score: float
    trend_status: str
    dominant_fault_type: str
    dominant_pattern_id: str
    hotspot_id: str | None = None
    cluster_id: str | None = None
    engineering_recommendation: str
    analyzed_at: str | None = None


class AnalyzeDieResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed"]
    config_version: str = ""
    upstream_execution_ids: dict = Field(default_factory=dict)
    source_record_count: int = 0
    die_count: int = 0
    failing_die_count: int = 0
    hotspot_count: int = 0
    cluster_count: int = 0
    processing_ms: float = 0.0
    dies: list[DieSummary] = Field(default_factory=list)
    hotspots: list[dict] = Field(default_factory=list)
    clusters: list[dict] = Field(default_factory=list)
    statistics: dict = Field(default_factory=dict)
    benchmark_metrics: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
