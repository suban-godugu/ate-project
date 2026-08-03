"""Scan Chain pipeline persistence models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ParserJobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped_duplicate = "skipped_duplicate"


class ParserJob(Base):
    __tablename__ = "parser_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ParserJobStatus] = mapped_column(
        Enum(ParserJobStatus, name="parser_job_status"), nullable=False, default=ParserJobStatus.pending
    )
    parser_id: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float)
    vendor: Mapped[str | None] = mapped_column(String(64))
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("parser_jobs.id"))
    error_message: Mapped[str | None] = mapped_column(Text)
    unified_dataset_key: Mapped[str | None] = mapped_column(String(1024))
    failed_stage: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    statistics: Mapped["ParserStatistics | None"] = relationship(back_populates="parser_job", uselist=False)
    parsed_files: Mapped[list["ParsedFile"]] = relationship(back_populates="parser_job", cascade="all, delete-orphan")


class ParserStatistics(Base):
    __tablename__ = "parser_statistics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parser_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parser_jobs.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    parse_time_ms: Mapped[float | None] = mapped_column(Float)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    quarantine_count: Mapped[int] = mapped_column(Integer, default=0)
    throughput_records_per_s: Mapped[float | None] = mapped_column(Float)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    extras: Mapped[dict | None] = mapped_column(JSONB)

    parser_job: Mapped["ParserJob"] = relationship(back_populates="statistics")


class ParsedFile(Base):
    __tablename__ = "parsed_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parser_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parser_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(32))
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64))
    parser_id: Mapped[str | None] = mapped_column(String(64))
    minio_bucket: Mapped[str | None] = mapped_column(String(128))
    minio_object_key: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parser_job: Mapped["ParserJob"] = relationship(back_populates="parsed_files")


class NormalizedRecord(Base):
    __tablename__ = "normalized_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parser_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parser_jobs.id", ondelete="SET NULL"), index=True
    )
    parsed_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parsed_files.id", ondelete="SET NULL")
    )
    lot_id: Mapped[str | None] = mapped_column(String(128), index=True)
    wafer_id: Mapped[str | None] = mapped_column(String(128), index=True)
    die_id: Mapped[str | None] = mapped_column(String(128), index=True)
    pass_fail: Mapped[str | None] = mapped_column(String(16), index=True)
    scan_chain: Mapped[str | None] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PatternResult(Base):
    __tablename__ = "pattern_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    agent_job_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    report: Mapped[dict | None] = mapped_column(JSONB)
    kpis: Mapped[dict | None] = mapped_column(JSONB)
    artifact_key: Mapped[str | None] = mapped_column(String(1024))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FailureResult(Base):
    __tablename__ = "failure_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    agent_job_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    report: Mapped[dict | None] = mapped_column(JSONB)
    yield_report: Mapped[dict | None] = mapped_column(JSONB)
    kpis: Mapped[dict | None] = mapped_column(JSONB)
    artifact_key: Mapped[str | None] = mapped_column(String(1024))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    agent_job_id: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    report: Mapped[dict | None] = mapped_column(JSONB)
    kpis: Mapped[dict | None] = mapped_column(JSONB)
    recommendations: Mapped[dict | None] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(Float)
    artifact_key: Mapped[str | None] = mapped_column(String(1024))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload: Mapped[dict | None] = mapped_column(JSONB)
    kpis: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DashboardMetric(Base):
    __tablename__ = "dashboard_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    executive_kpis: Mapped[dict | None] = mapped_column(JSONB)
    pattern_kpis: Mapped[dict | None] = mapped_column(JSONB)
    failure_kpis: Mapped[dict | None] = mapped_column(JSONB)
    diagnosis_kpis: Mapped[dict | None] = mapped_column(JSONB)
    recommendation_kpis: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent: Mapped[str | None] = mapped_column(String(64))
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    extras: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
