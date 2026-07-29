"""Scan Chain pipeline tables

Revision ID: 004_scan_chain_pipeline
Revises: 003_rl_training
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_scan_chain_pipeline"
down_revision: Union[str, None] = "003_rl_training"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum may already exist from a partial prior migration run.
    parser_job_status = postgresql.ENUM(
        "pending",
        "running",
        "completed",
        "failed",
        "skipped_duplicate",
        name="parser_job_status",
        create_type=False,
    )
    op.execute(
        "DO $$ BEGIN "
        "CREATE TYPE parser_job_status AS ENUM "
        "('pending', 'running', 'completed', 'failed', 'skipped_duplicate'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    )

    op.create_table(
        "parser_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", parser_job_status, nullable=False, server_default="pending"),
        sa.Column("parser_id", sa.String(64)),
        sa.Column("confidence", sa.Float()),
        sa.Column("vendor", sa.String(64)),
        sa.Column("sha256", sa.String(64)),
        sa.Column("duplicate_of", postgresql.UUID(as_uuid=True), sa.ForeignKey("parser_jobs.id")),
        sa.Column("error_message", sa.Text()),
        sa.Column("unified_dataset_key", sa.String(1024)),
        sa.Column("failed_stage", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_parser_jobs_upload_job_id", "parser_jobs", ["upload_job_id"])
    op.create_index("ix_parser_jobs_sha256", "parser_jobs", ["sha256"])

    op.create_table(
        "parser_statistics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parser_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parser_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("parse_time_ms", sa.Float()),
        sa.Column("record_count", sa.Integer(), server_default="0"),
        sa.Column("quarantine_count", sa.Integer(), server_default="0"),
        sa.Column("throughput_records_per_s", sa.Float()),
        sa.Column("cache_hit", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("error_count", sa.Integer(), server_default="0"),
        sa.Column("extras", postgresql.JSONB()),
    )

    op.create_table(
        "parsed_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parser_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parser_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upload_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(32)),
        sa.Column("size_bytes", sa.BigInteger(), server_default="0"),
        sa.Column("sha256", sa.String(64)),
        sa.Column("parser_id", sa.String(64)),
        sa.Column("minio_bucket", sa.String(128)),
        sa.Column("minio_object_key", sa.String(1024)),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_parsed_files_parser_job_id", "parsed_files", ["parser_job_id"])
    op.create_index("ix_parsed_files_upload_job_id", "parsed_files", ["upload_job_id"])

    op.create_table(
        "normalized_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parser_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parser_jobs.id", ondelete="SET NULL")),
        sa.Column("parsed_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("parsed_files.id", ondelete="SET NULL")),
        sa.Column("lot_id", sa.String(128)),
        sa.Column("wafer_id", sa.String(128)),
        sa.Column("die_id", sa.String(128)),
        sa.Column("pass_fail", sa.String(16)),
        sa.Column("scan_chain", sa.String(128)),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_normalized_records_upload_job_id", "normalized_records", ["upload_job_id"])
    op.create_index("ix_normalized_records_lot_id", "normalized_records", ["lot_id"])
    op.create_index("ix_normalized_records_wafer_id", "normalized_records", ["wafer_id"])
    op.create_index("ix_normalized_records_die_id", "normalized_records", ["die_id"])
    op.create_index("ix_normalized_records_pass_fail", "normalized_records", ["pass_fail"])
    op.create_index("ix_normalized_records_scan_chain", "normalized_records", ["scan_chain"])

    for table, cols in (
        (
            "pattern_results",
            [
                sa.Column("agent_job_id", sa.String(128)),
                sa.Column("status", sa.String(32), server_default="pending"),
                sa.Column("report", postgresql.JSONB()),
                sa.Column("kpis", postgresql.JSONB()),
                sa.Column("artifact_key", sa.String(1024)),
                sa.Column("error_message", sa.Text()),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                sa.Column("completed_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "failure_results",
            [
                sa.Column("agent_job_id", sa.String(128)),
                sa.Column("status", sa.String(32), server_default="pending"),
                sa.Column("report", postgresql.JSONB()),
                sa.Column("yield_report", postgresql.JSONB()),
                sa.Column("kpis", postgresql.JSONB()),
                sa.Column("artifact_key", sa.String(1024)),
                sa.Column("error_message", sa.Text()),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                sa.Column("completed_at", sa.DateTime(timezone=True)),
            ],
        ),
        (
            "diagnosis_results",
            [
                sa.Column("agent_job_id", sa.String(128)),
                sa.Column("status", sa.String(32), server_default="pending"),
                sa.Column("report", postgresql.JSONB()),
                sa.Column("kpis", postgresql.JSONB()),
                sa.Column("recommendations", postgresql.JSONB()),
                sa.Column("confidence", sa.Float()),
                sa.Column("artifact_key", sa.String(1024)),
                sa.Column("error_message", sa.Text()),
                sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                sa.Column("completed_at", sa.DateTime(timezone=True)),
            ],
        ),
    ):
        op.create_table(
            table,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "upload_job_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            *cols,
        )

    op.create_table(
        "recommendation_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "upload_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("payload", postgresql.JSONB()),
        sa.Column("kpis", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "dashboard_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "upload_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("executive_kpis", postgresql.JSONB()),
        sa.Column("pattern_kpis", postgresql.JSONB()),
        sa.Column("failure_kpis", postgresql.JSONB()),
        sa.Column("diagnosis_kpis", postgresql.JSONB()),
        sa.Column("recommendation_kpis", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "agent_execution_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "upload_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("upload_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("agent", sa.String(64)),
        sa.Column("attempt", sa.Integer(), server_default="1"),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("extras", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_agent_execution_logs_upload_job_id", "agent_execution_logs", ["upload_job_id"])
    op.create_index("ix_agent_execution_logs_stage", "agent_execution_logs", ["stage"])


def downgrade() -> None:
    op.drop_table("agent_execution_logs")
    op.drop_table("dashboard_metrics")
    op.drop_table("recommendation_results")
    op.drop_table("diagnosis_results")
    op.drop_table("failure_results")
    op.drop_table("pattern_results")
    op.drop_table("normalized_records")
    op.drop_table("parsed_files")
    op.drop_table("parser_statistics")
    op.drop_table("parser_jobs")
    op.execute("DROP TYPE IF EXISTS parser_job_status")
