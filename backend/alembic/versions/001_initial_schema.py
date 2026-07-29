"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-07-03
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fabs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "testers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("platform", sa.String(64)),
        sa.Column("fab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fabs.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "lots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lot_code", sa.String(64), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("fab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fabs.id")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "wafers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("wafer_code", sa.String(64), nullable=False),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("slot", sa.Integer()),
        sa.Column("yield_pct", sa.Numeric(5, 2)),
        sa.Column("good_dies", sa.Integer()),
        sa.Column("bad_dies", sa.Integer()),
        sa.Column("total_dies", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("role", sa.String(64), server_default="engineer"),
        sa.Column("department", sa.String(128)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "user_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("theme_json", postgresql.JSONB()),
        sa.Column("account_json", postgresql.JSONB()),
        sa.Column("filters_json", postgresql.JSONB()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64)),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("meta", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    upload_status = postgresql.ENUM(
        "queued", "uploading", "parsing", "processing", "completed", "failed",
        name="upload_status",
        create_type=False,
    )
    upload_kind = postgresql.ENUM("data", "log", name="upload_kind", create_type=False)
    upload_status.create(op.get_bind(), checkfirst=True)
    upload_kind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "upload_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", upload_kind, nullable=False),
        sa.Column("module", sa.String(64), nullable=False),
        sa.Column("status", upload_status, nullable=False, server_default="queued"),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(32)),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("fab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fabs.id")),
        sa.Column("tester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("testers.id")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("wafer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wafers.id")),
        sa.Column("minio_bucket", sa.String(128), nullable=False),
        sa.Column("minio_object_key", sa.String(1024), nullable=False),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("processing_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "upload_pipeline_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_jobs.id", ondelete="CASCADE")),
        sa.Column("step_key", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("meta", postgresql.JSONB()),
    )
    op.create_table(
        "ai_log_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_jobs.id"), unique=True),
        sa.Column("files_processed", sa.Integer()),
        sa.Column("patterns_found", sa.Integer()),
        sa.Column("scan_chains", sa.Integer()),
        sa.Column("memory_blocks", sa.Integer()),
        sa.Column("logic_blocks", sa.Integer()),
        sa.Column("wafer_count", sa.Integer()),
        sa.Column("defects_found", sa.Integer()),
        sa.Column("yield_pct", sa.Numeric(5, 2)),
        sa.Column("estimated_cost", sa.Numeric(14, 2)),
        sa.Column("estimated_savings", sa.Numeric(14, 2)),
        sa.Column("raw_summary_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "kpi_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module", sa.String(32), nullable=False),
        sa.Column("kpi_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(128)),
        sa.Column("value_text", sa.String(64)),
        sa.Column("value_num", sa.Numeric(18, 4)),
        sa.Column("change_pct", sa.Numeric(8, 2)),
        sa.Column("trend", sa.String(8)),
        sa.Column("sparkline", postgresql.JSONB()),
        sa.Column("fab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fabs.id")),
        sa.Column("tester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("testers.id")),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("wafer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wafers.id")),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_kpi_snapshots_filter", "kpi_snapshots", ["module", sa.text("captured_at DESC")])

    op.create_table(
        "scan_chain_failures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("chain_id", sa.String(64)),
        sa.Column("pattern_id", sa.String(64)),
        sa.Column("chip", sa.String(64)),
        sa.Column("fail_cycle", sa.Integer()),
        sa.Column("fail_type", sa.String(64)),
        sa.Column("root_cause", sa.Text()),
        sa.Column("diagnosis_status", sa.String(32)),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("wafer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wafers.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    wafer_defect_class = postgresql.ENUM(
        "centre", "donut", "edge-ring", "scratch", "near-full", "normal", "edge-loc", "local", "random",
        name="wafer_defect_class",
        create_type=False,
    )
    wafer_defect_class.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "wafer_defect_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("defect_class", wafer_defect_class, nullable=False),
        sa.Column("upload_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_jobs.id")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("wafer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wafers.id")),
        sa.Column("confidence", sa.Numeric(5, 2)),
        sa.Column("yield_pct", sa.Numeric(5, 2)),
        sa.Column("seed", sa.Integer()),
        sa.Column("hotspot_x", sa.Integer()),
        sa.Column("hotspot_y", sa.Integer()),
        sa.Column("image_wafer_key", sa.String(1024)),
        sa.Column("image_overlay_key", sa.String(1024)),
        sa.Column("image_density_key", sa.String(1024)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_wafer_defect_class", "wafer_defect_uploads", ["defect_class", sa.text("created_at DESC")])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_module", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="Open"),
        sa.Column("title", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("wafer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wafers.id")),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_alerts_created", "alerts", [sa.text("created_at DESC")])
    op.create_index("idx_alerts_lot", "alerts", ["lot_id", sa.text("created_at DESC")])

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_type", sa.String(64)),
        sa.Column("category", sa.String(64)),
        sa.Column("priority", sa.String(16)),
        sa.Column("confidence", sa.Numeric(5, 2)),
        sa.Column("expected_impact", sa.Text()),
        sa.Column("action_text", sa.Text()),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("assigned_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("severity", sa.String(16)),
        sa.Column("title", sa.String(256)),
        sa.Column("message", sa.Text()),
        sa.Column("read", sa.Boolean(), server_default="false"),
        sa.Column("alert_route", sa.String(256)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "recommendation_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendations.id", ondelete="CASCADE")),
        sa.Column("agent_type", sa.String(64), nullable=False),
        sa.Column("action_taken", sa.String(32), nullable=False),
        sa.Column("outcome_metric", sa.String(64)),
        sa.Column("outcome_value", sa.Numeric(14, 4)),
        sa.Column("reward_value", sa.Numeric(8, 4)),
        sa.Column("model_version", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_rec_feedback_agent", "recommendation_feedback", ["agent_type", sa.text("created_at DESC")])
    op.create_index("idx_upload_jobs_status", "upload_jobs", ["status", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("recommendation_feedback")
    op.drop_table("notifications")
    op.drop_table("recommendations")
    op.drop_table("alerts")
    op.drop_table("wafer_defect_uploads")
    op.drop_table("scan_chain_failures")
    op.drop_table("kpi_snapshots")
    op.drop_table("ai_log_summaries")
    op.drop_table("upload_pipeline_steps")
    op.drop_table("upload_jobs")
    op.drop_table("audit_logs")
    op.drop_table("user_preferences")
    op.drop_table("users")
    op.drop_table("wafers")
    op.drop_table("lots")
    op.drop_table("testers")
    op.drop_table("products")
    op.drop_table("fabs")
    sa.Enum(name="upload_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="upload_kind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="wafer_defect_class").drop(op.get_bind(), checkfirst=True)
