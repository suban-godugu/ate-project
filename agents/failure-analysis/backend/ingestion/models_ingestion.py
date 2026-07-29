"""FA-FR-001 production ingestion models (additive schema)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


class IngestionDataset(Base):
    """Folder / multi-file dataset grouping STIL + tester logs."""

    __tablename__ = "ingestion_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(512), index=True)
    source_root: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    stil_count: Mapped[int] = mapped_column(Integer, default=0)
    log_count: Mapped[int] = mapped_column(Integer, default=0)
    records_accepted: Mapped[int] = mapped_column(Integer, default=0)
    records_quarantined: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UploadHistory(Base):
    """Append-only lifecycle transitions for an upload."""

    __tablename__ = "upload_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    upload_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("uploads.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ParserMetadata(Base):
    """Parser-specific extracted metadata (STIL chains, CSV mapping, etc.)."""

    __tablename__ = "parser_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    upload_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("uploads.id", ondelete="CASCADE"), index=True
    )
    parser_id: Mapped[str] = mapped_column(String(64), index=True)
    parser_version: Mapped[str] = mapped_column(String(32), default="1.0")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ValidationResult(Base):
    """Persisted file / record validation outcomes."""

    __tablename__ = "validation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    upload_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("uploads.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ingestion_datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    severity: Mapped[str] = mapped_column(String(16), default="error", index=True)
    category: Mapped[str] = mapped_column(String(64), default="validation")
    code: Mapped[str] = mapped_column(String(64), default="GENERIC")
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class NormalizedRecord(Base):
    """Canonical normalized semiconductor test records (production table)."""

    __tablename__ = "normalized_records"
    __table_args__ = (
        UniqueConstraint("upload_id", "record_key", name="uq_normalized_upload_record_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    upload_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("uploads.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ingestion_datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    record_key: Mapped[str] = mapped_column(String(512), index=True)
    lot_id: Mapped[str] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str] = mapped_column(String(128), index=True)
    die_id: Mapped[str] = mapped_column(String(128), index=True)
    test_stage: Mapped[str] = mapped_column(String(64))
    tester_id: Mapped[str] = mapped_column(String(128))
    pass_fail: Mapped[str] = mapped_column(String(16), index=True)
    timestamp: Mapped[str] = mapped_column(String(64))
    adapter_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AuditLog(Base):
    """Structured security / operational audit trail."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class IngestionStatistics(Base):
    """Aggregated ingestion performance statistics per upload/dataset."""

    __tablename__ = "ingestion_statistics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    upload_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("uploads.id", ondelete="CASCADE"), nullable=True, index=True
    )
    dataset_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ingestion_datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    upload_ms: Mapped[float] = mapped_column(Float, default=0.0)
    validation_ms: Mapped[float] = mapped_column(Float, default=0.0)
    parse_ms: Mapped[float] = mapped_column(Float, default=0.0)
    normalize_ms: Mapped[float] = mapped_column(Float, default=0.0)
    persist_ms: Mapped[float] = mapped_column(Float, default=0.0)
    total_ms: Mapped[float] = mapped_column(Float, default=0.0)
    records_parsed: Mapped[int] = mapped_column(Integer, default=0)
    records_accepted: Mapped[int] = mapped_column(Integer, default=0)
    records_quarantined: Mapped[int] = mapped_column(Integer, default=0)
    records_per_minute: Mapped[float] = mapped_column(Float, default=0.0)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    parser_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
