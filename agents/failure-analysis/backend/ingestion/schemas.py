"""Pydantic v2 API schemas for FA-FR-001 OpenAPI documentation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UploadSummary(BaseModel):
    id: str
    dataset_id: str | None = None
    original_filename: str
    status: str
    parser_id: str | None = None
    records_accepted: int = 0
    records_quarantined: int = 0
    integrity_pct: float = 0.0
    file_size_bytes: int = 0
    checksum_sha256: str | None = None
    created_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class UploadResponse(BaseModel):
    duplicate: bool = False
    upload: UploadSummary
    parsed_dataset_preview: list[dict[str, Any]] = Field(default_factory=list)
    validation_report: dict[str, Any] = Field(default_factory=dict)
    processing_statistics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] | None = None


class AsyncUploadAccepted(BaseModel):
    upload_id: str
    dataset_id: str | None = None
    status: str
    message: str


class DatasetCreateResponse(BaseModel):
    dataset_id: str
    name: str
    status: str
    file_count: int
    stil_count: int
    log_count: int
    uploads: list[UploadSummary] = Field(default_factory=list)


class DatasetSummary(BaseModel):
    id: str
    name: str
    status: str
    file_count: int
    stil_count: int
    log_count: int
    records_accepted: int
    records_quarantined: int
    created_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class ValidationIssue(BaseModel):
    severity: str
    category: str
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ParserStat(BaseModel):
    parser_id: str
    upload_count: int
    records_accepted: int
    success_count: int


class IngestionStatsSummary(BaseModel):
    total_uploads: int
    completed: int
    failed: int
    queued: int
    processing: int
    total_records_accepted: int
    by_parser: list[ParserStat] = Field(default_factory=list)
