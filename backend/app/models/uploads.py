import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UploadStatus(str, enum.Enum):
    queued = "queued"
    uploading = "uploading"
    parsing = "parsing"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class UploadKind(str, enum.Enum):
    data = "data"
    log = "log"


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[UploadKind] = mapped_column(Enum(UploadKind, name="upload_kind"), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, name="upload_status"), nullable=False, default=UploadStatus.queued
    )
    file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(32))
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    fab_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fabs.id"))
    tester_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("testers.id"))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.id"))
    wafer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wafers.id"))
    minio_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    processing_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    pipeline_steps: Mapped[list["UploadPipelineStep"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    ai_summary: Mapped["AILogSummary | None"] = relationship(back_populates="upload_job", uselist=False)


class UploadPipelineStep(Base):
    __tablename__ = "upload_pipeline_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("upload_jobs.id", ondelete="CASCADE"))
    step_key: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meta: Mapped[dict | None] = mapped_column(JSONB)

    job: Mapped["UploadJob"] = relationship(back_populates="pipeline_steps")


class AILogSummary(Base):
    __tablename__ = "ai_log_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    upload_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("upload_jobs.id"), unique=True)
    files_processed: Mapped[int | None] = mapped_column(Integer)
    patterns_found: Mapped[int | None] = mapped_column(Integer)
    scan_chains: Mapped[int | None] = mapped_column(Integer)
    memory_blocks: Mapped[int | None] = mapped_column(Integer)
    logic_blocks: Mapped[int | None] = mapped_column(Integer)
    wafer_count: Mapped[int | None] = mapped_column(Integer)
    defects_found: Mapped[int | None] = mapped_column(Integer)
    yield_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(14, 2))
    estimated_savings: Mapped[float | None] = mapped_column(Numeric(14, 2))
    raw_summary_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    upload_job: Mapped["UploadJob | None"] = relationship(back_populates="ai_summary")
