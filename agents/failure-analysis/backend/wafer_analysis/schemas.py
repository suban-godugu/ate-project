"""Pydantic v2 contracts for production FA-FR-008."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalyzeWaferRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    detection_execution_id: str | None = Field(default=None, max_length=36)
    computation_id: str | None = Field(default=None, max_length=36)
    recurrence_analysis_id: str | None = Field(default=None, max_length=36)
    correlation_analysis_id: str | None = Field(default=None, max_length=36)
    die_analysis_id: str | None = Field(default=None, max_length=36)
    historical_window: int = Field(default=50, ge=2, le=500)
    hotspot_density_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    edge_radius_fraction: float | None = Field(default=None, gt=0.0, le=1.0)
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    incremental: bool = True
    async_execution: bool = False
    expected_failing_wafer_ids: list[str] = Field(default_factory=list)
    expected_passing_wafer_ids: list[str] = Field(default_factory=list)
    actor: str | None = Field(default=None, max_length=128)
    legacy: bool = Field(
        default=False,
        description="When true, dispatches to the legacy /api/v1/wafer analyzer.",
    )

    @model_validator(mode="after")
    def validate_source(self) -> "AnalyzeWaferRequest":
        if self.legacy:
            if not self.upload_id:
                raise ValueError("legacy mode requires upload_id")
            return self
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class WaferSummary(BaseModel):
    wafer_result_id: str
    analysis_id: str
    lot_id: str
    wafer_id: str
    total_dies: int
    failing_dies: int
    yield_pct: float
    failure_density: float
    edge_failure_rate: float
    center_failure_rate: float
    health_score: float
    severity: str
    confidence_score: float
    trend_status: str
    engineering_recommendation: str
    analyzed_at: str | None = None


class AnalyzeWaferResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed"]
    config_version: str = ""
    upstream_execution_ids: dict = Field(default_factory=dict)
    source_die_count: int = 0
    wafer_count: int = 0
    failing_wafer_count: int = 0
    hotspot_count: int = 0
    processing_ms: float = 0.0
    wafers: list[WaferSummary] = Field(default_factory=list)
    hotspots: list[dict] = Field(default_factory=list)
    yield_metrics: list[dict] = Field(default_factory=list)
    statistics: dict = Field(default_factory=dict)
    benchmark_metrics: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
