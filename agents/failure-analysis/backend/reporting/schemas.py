"""Pydantic v2 contracts for production FA-FR-010 reporting."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ExportFormat = Literal["pdf", "html", "csv", "xlsx", "json"]


class GenerateReportRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = None
    template_key: str | None = Field(default=None, max_length=64)
    report_name: str | None = Field(default=None, max_length=256)
    config_path: str | None = None
    incremental: bool = True
    async_execution: bool = False
    actor: str | None = Field(default=None, max_length=128)
    legacy: bool = Field(
        default=False,
        description="When true, dispatches to legacy upload-only report generator.",
    )

    @model_validator(mode="after")
    def validate_source(self) -> "GenerateReportRequest":
        if self.legacy:
            if not self.upload_id:
                raise ValueError("legacy mode requires upload_id")
            return self
        if bool(self.dataset_id) == bool(self.upload_id):
            raise ValueError("Exactly one of dataset_id or upload_id is required")
        return self


class ExportReportRequest(BaseModel):
    report_id: str = Field(..., max_length=36)
    format: ExportFormat
    async_execution: bool = False
    actor: str | None = Field(default=None, max_length=128)


class ReportSummary(BaseModel):
    report_id: str
    report_name: str
    report_version: int
    dataset_id: str | None = None
    upload_id: str | None = None
    status: str
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    processing_ms: float = 0.0
    created_at: str | None = None
    completed_at: str | None = None
    legacy: bool = False


class GenerateReportResponse(BaseModel):
    report_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    upload_id: str | None = None
    dataset_id: str | None = None
    template_key: str | None = None
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    processing_ms: float = 0.0
    meets_performance_target: bool = False
    executive_report: dict = Field(default_factory=dict)
    engineering_report: dict = Field(default_factory=dict)
    benchmark_summary: dict = Field(default_factory=dict)
    recommendations: list = Field(default_factory=list)
    dashboard_dataset: dict = Field(default_factory=dict)
    export_paths: dict = Field(default_factory=dict)
    traceability: dict = Field(default_factory=dict)
    upstream_execution_ids: dict = Field(default_factory=dict)


class ExportReportResponse(BaseModel):
    export_id: str
    report_id: str
    format: ExportFormat
    status: str
    file_path: str | None = None
    file_size_bytes: int = 0
    processing_ms: float = 0.0


class ReportTemplateResponse(BaseModel):
    template_id: str
    template_key: str
    name: str
    version: str
    description: str = ""
    sections: dict = Field(default_factory=dict)
    is_default: bool = False
