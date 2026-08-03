import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WaferDefectClass(str, enum.Enum):
    centre = "centre"
    donut = "donut"
    edge_ring = "edge-ring"
    scratch = "scratch"
    near_full = "near-full"
    normal = "normal"
    edge_loc = "edge-loc"
    local = "local"
    random = "random"


class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    kpi_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str | None] = mapped_column(String(128))
    value_text: Mapped[str | None] = mapped_column(String(64))
    value_num: Mapped[float | None] = mapped_column(Numeric(18, 4))
    change_pct: Mapped[float | None] = mapped_column(Numeric(8, 2))
    trend: Mapped[str | None] = mapped_column(String(8))
    sparkline: Mapped[list | None] = mapped_column(JSONB)
    fab_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("fabs.id"))
    tester_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("testers.id"))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.id"))
    wafer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wafers.id"))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScanChainFailure(Base):
    __tablename__ = "scan_chain_failures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_id: Mapped[str | None] = mapped_column(String(64))
    pattern_id: Mapped[str | None] = mapped_column(String(64))
    chip: Mapped[str | None] = mapped_column(String(64))
    fail_cycle: Mapped[int | None] = mapped_column(Integer)
    fail_type: Mapped[str | None] = mapped_column(String(64))
    root_cause: Mapped[str | None] = mapped_column(Text)
    diagnosis_status: Mapped[str | None] = mapped_column(String(32))
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.id"))
    wafer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wafers.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


wafer_defect_enum = Enum(
    WaferDefectClass,
    name="wafer_defect_class",
    values_callable=lambda members: [member.value for member in members],
)


class WaferDefectUpload(Base):
    __tablename__ = "wafer_defect_uploads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_class: Mapped[WaferDefectClass] = mapped_column(wafer_defect_enum, nullable=False)
    upload_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("upload_jobs.id"))
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.id"))
    wafer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wafers.id"))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    yield_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    seed: Mapped[int | None] = mapped_column(Integer)
    hotspot_x: Mapped[int | None] = mapped_column(Integer)
    hotspot_y: Mapped[int | None] = mapped_column(Integer)
    image_wafer_key: Mapped[str | None] = mapped_column(String(1024))
    image_overlay_key: Mapped[str | None] = mapped_column(String(1024))
    image_density_key: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_module: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Open")
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.id"))
    wafer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("wafers.id"))
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    severity: Mapped[str | None] = mapped_column(String(16))
    title: Mapped[str | None] = mapped_column(String(256))
    message: Mapped[str | None] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_route: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
