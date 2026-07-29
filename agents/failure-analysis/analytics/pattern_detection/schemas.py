"""Pydantic v2 API contracts for FA-FR-002."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DetectPatternsRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    async_execution: bool = False
    incremental: bool = True
    confidence_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    customer_id: str | None = Field(default=None, max_length=128)
    actor: str | None = Field(default=None, max_length=128)
    expected_pattern_ids: list[str] | None = Field(
        default=None,
        description="Optional labeled ground truth used only for benchmark metrics.",
    )

    @model_validator(mode="after")
    def exactly_one_source(self) -> "DetectPatternsRequest":
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class PatternSummary(BaseModel):
    id: str
    analysis_id: str
    dataset_id: str | None = None
    pattern_id: str
    pattern_name: str
    pattern_category: str
    pattern_frequency: float
    confidence: float
    detection_method: str
    severity_level: str
    failure_count: int
    affected_device_count: int
    affected_die_count: int
    affected_wafer_count: int
    affected_lot_count: int
    created_at: str | None = None


class DetectPatternsResponse(BaseModel):
    execution_id: str
    dataset_id: str | None = None
    upload_id: str | None = None
    status: Literal["queued", "processing", "completed", "failed"]
    pattern_count: int = 0
    source_record_count: int = 0
    processing_ms: float = 0.0
    rule_set_version: str = ""
    patterns: list[PatternSummary] = Field(default_factory=list)
    benchmark_metrics: dict[str, float | int | None] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class RuleCreateRequest(BaseModel):
    rule_key: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=1, max_length=256)
    category: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    customer_id: str | None = Field(default=None, max_length=128)
    priority: int = Field(default=100, ge=0, le=10000)
    severity_level: Literal["low", "medium", "high", "critical"] = "medium"
    confidence_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    definition: dict
    explanation_template: str = Field(default="", max_length=4000)
    created_by: str | None = Field(default=None, max_length=128)
