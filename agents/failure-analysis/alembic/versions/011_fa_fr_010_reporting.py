"""Add production FA-FR-010 enterprise reporting persistence.

Revision ID: 011_fa_fr_010_reporting
Revises: 010_fa_fr_009_fault_prediction
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "011_fa_fr_010_reporting"
down_revision: Union[str, None] = "010_fa_fr_009_fault_prediction"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _indexes(table: str) -> set[str]:
    return {item["name"] for item in inspect(op.get_bind()).get_indexes(table)}


def _index(table: str, column: str) -> None:
    name = f"ix_{table}_{column}"
    if name not in _indexes(table):
        op.create_index(name, table, [column])


def upgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())

    if "report_templates" not in tables:
        op.create_table(
            "report_templates",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("template_key", sa.String(64), nullable=False, unique=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("version", sa.String(64), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("sections_json", sa.JSON(), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("template_key", "version", "is_default"):
        _index("report_templates", column)

    if "reports" not in tables:
        op.create_table(
            "reports",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("report_name", sa.String(256), nullable=False),
            sa.Column("report_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("template_id", sa.String(36), nullable=True),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("completeness_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("consistency_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("traceability_json", sa.JSON(), nullable=False),
            sa.Column("upstream_execution_ids", sa.JSON(), nullable=False),
            sa.Column("report_json", sa.JSON(), nullable=False),
            sa.Column("dashboard_json", sa.JSON(), nullable=False),
            sa.Column("executive_summary", sa.JSON(), nullable=False),
            sa.Column("engineering_summary", sa.JSON(), nullable=False),
            sa.Column("benchmark_summary", sa.JSON(), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False, server_default=""),
            sa.Column("actor", sa.String(128), nullable=True),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("pdf_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("excel_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("export_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
    for column in (
        "template_id",
        "dataset_id",
        "upload_id",
        "status",
        "created_at",
    ):
        _index("reports", column)

    if "report_history" not in tables:
        op.create_table(
            "report_history",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("report_id", sa.String(36), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("snapshot_json", sa.JSON(), nullable=False),
            sa.Column("change_reason", sa.String(256), nullable=False, server_default=""),
            sa.Column("actor", sa.String(128), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("report_id", "version", name="uq_report_history_version"),
        )
    for column in ("report_id", "version", "created_at"):
        _index("report_history", column)

    if "report_exports" not in tables:
        op.create_table(
            "report_exports",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("export_id", sa.String(36), nullable=False, unique=True),
            sa.Column("report_id", sa.String(36), nullable=False),
            sa.Column("format", sa.String(16), nullable=False),
            sa.Column("file_path", sa.String(1024), nullable=False, server_default=""),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("actor", sa.String(128), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("export_id", "report_id", "format", "status", "created_at"):
        _index("report_exports", column)

    if "benchmark_results" not in tables:
        op.create_table(
            "benchmark_results",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("report_id", sa.String(36), nullable=False),
            sa.Column("benchmark_type", sa.String(64), nullable=False),
            sa.Column("metric_name", sa.String(128), nullable=False),
            sa.Column("metric_value", sa.Float(), nullable=False, server_default="0"),
            sa.Column("target_value", sa.Float(), nullable=True),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("report_id", "benchmark_type", "metric_name", "created_at"):
        _index("benchmark_results", column)

    if "report_audit_logs" not in tables:
        op.create_table(
            "report_audit_logs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("report_id", sa.String(36), nullable=True),
            sa.Column("action", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("actor", sa.String(128), nullable=True),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("template_id", sa.String(36), nullable=True),
            sa.Column("export_format", sa.String(16), nullable=True),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("errors", sa.JSON(), nullable=False),
            sa.Column("warnings", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("benchmark_metrics", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
    for column in (
        "report_id",
        "action",
        "status",
        "dataset_id",
        "upload_id",
        "created_at",
    ):
        _index("report_audit_logs", column)

    if "engineering_recommendations" in tables:
        columns = {col["name"] for col in inspect(op.get_bind()).get_columns("engineering_recommendations")}
        if "report_id" not in columns:
            op.add_column(
                "engineering_recommendations",
                sa.Column("report_id", sa.String(36), nullable=True),
            )
            _index("engineering_recommendations", "report_id")


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "engineering_recommendations" in tables:
        columns = {col["name"] for col in inspect(op.get_bind()).get_columns("engineering_recommendations")}
        if "report_id" in columns:
            op.drop_index("ix_engineering_recommendations_report_id", table_name="engineering_recommendations")
            op.drop_column("engineering_recommendations", "report_id")
    for table in (
        "report_audit_logs",
        "benchmark_results",
        "report_exports",
        "report_history",
        "reports",
        "report_templates",
    ):
        if table in tables:
            op.drop_table(table)
