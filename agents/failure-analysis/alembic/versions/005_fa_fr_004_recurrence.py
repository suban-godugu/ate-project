"""FA-FR-004 production recurring failure analysis schema.

Revision ID: 005_fa_fr_004_recurrence
Revises: 004_fa_fr_003_failure_rates
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "005_fa_fr_004_recurrence"
down_revision: Union[str, None] = "004_fa_fr_003_failure_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _index(table: str, name: str, columns: list[str]) -> None:
    current = {item["name"] for item in inspect(op.get_bind()).get_indexes(table)}
    if name not in current:
        op.create_index(name, table, columns)


def upgrade() -> None:
    existing = _tables()
    if "recurring_failures" not in existing:
        op.create_table(
            "recurring_failures",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("recurrence_id", sa.String(36), nullable=False, unique=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("detected_pattern_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("pattern_name", sa.String(256), nullable=False, server_default=""),
            sa.Column("signature_hash", sa.String(64), nullable=False),
            sa.Column("similarity_group", sa.String(64)),
            sa.Column("recurrence_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("recurrence_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("severity", sa.String(32), nullable=False, server_default="low"),
            sa.Column("trend_direction", sa.String(32), nullable=False, server_default="stable"),
            sa.Column("first_occurrence", sa.DateTime(timezone=True), nullable=False),
            sa.Column("latest_occurrence", sa.DateTime(timezone=True), nullable=False),
            sa.Column("historical_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("hotspot_location", sa.JSON(), nullable=False),
            sa.Column("engineering_recommendation", sa.Text(), nullable=False, server_default=""),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("incremental", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "analysis_id",
                "pattern_id",
                "signature_hash",
                name="uq_recurring_failure_analysis_signature",
            ),
        )
    for column in (
        "recurrence_id", "analysis_id", "dataset_id", "upload_id",
        "detection_execution_id", "computation_id", "detected_pattern_id",
        "pattern_id", "signature_hash", "similarity_group", "severity",
        "trend_direction",
    ):
        _index("recurring_failures", f"ix_recurring_failures_{column}", [column])
    _index(
        "recurring_failures",
        "ix_recurring_failures_pattern_created",
        ["pattern_id", "created_at"],
    )

    if "recurrence_statistics" not in existing:
        op.create_table(
            "recurrence_statistics",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("scope_type", sa.String(32), nullable=False),
            sa.Column("scope_key", sa.String(512), nullable=False),
            sa.Column("pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recurrence_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("mean_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("mean_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("hotspot_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("analysis_id", "scope_type", "scope_key"):
        _index("recurrence_statistics", f"ix_recurrence_statistics_{column}", [column])

    if "recurrence_history" not in existing:
        op.create_table(
            "recurrence_history",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "recurrence_id",
                sa.String(36),
                sa.ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("occurrence_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_execution_ids", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("recurrence_id", "analysis_id", "pattern_id", "dataset_id", "upload_id"):
        _index("recurrence_history", f"ix_recurrence_history_{column}", [column])

    if "recurrence_trends" not in existing:
        op.create_table(
            "recurrence_trends",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "recurrence_id",
                sa.String(36),
                sa.ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("trend_direction", sa.String(32), nullable=False),
            sa.Column("current_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("historical_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("absolute_change", sa.Float(), nullable=False, server_default="0"),
            sa.Column("relative_change", sa.Float()),
            sa.Column("newly_emerging", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("time_series", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("recurrence_id", "analysis_id", "pattern_id", "trend_direction", "newly_emerging"):
        _index("recurrence_trends", f"ix_recurrence_trends_{column}", [column])

    if "hotspot_analysis" not in existing:
        op.create_table(
            "hotspot_analysis",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("hotspot_id", sa.String(36), nullable=False, unique=True),
            sa.Column(
                "recurrence_id",
                sa.String(36),
                sa.ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("wafer_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("x", sa.Integer()),
            sa.Column("y", sa.Integer()),
            sa.Column("radius", sa.Float(), nullable=False, server_default="0"),
            sa.Column("occurrence_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("severity", sa.String(32), nullable=False, server_default="low"),
            sa.Column("coordinates", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in (
        "hotspot_id", "recurrence_id", "analysis_id", "pattern_id",
        "lot_id", "wafer_id", "severity",
    ):
        _index("hotspot_analysis", f"ix_hotspot_analysis_{column}", [column])
    _index("hotspot_analysis", "ix_hotspot_analysis_wafer_xy", ["wafer_id", "x", "y"])

    if "recurrence_audit_logs" not in existing:
        op.create_table(
            "recurrence_audit_logs",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("detection_execution_id", sa.String(36)),
            sa.Column("computation_id", sa.String(36)),
            sa.Column("action", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False, server_default=""),
            sa.Column("source_record_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("recurrence_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("benchmark_metrics", sa.JSON(), nullable=False),
            sa.Column("errors", sa.JSON(), nullable=False),
            sa.Column("warnings", sa.JSON(), nullable=False),
            sa.Column("actor", sa.String(128)),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
        )
    for column in (
        "analysis_id", "dataset_id", "upload_id", "detection_execution_id",
        "computation_id", "action", "status",
    ):
        _index("recurrence_audit_logs", f"ix_recurrence_audit_logs_{column}", [column])


def downgrade() -> None:
    for table in (
        "recurrence_audit_logs",
        "hotspot_analysis",
        "recurrence_trends",
        "recurrence_history",
        "recurrence_statistics",
        "recurring_failures",
    ):
        if table in _tables():
            op.drop_table(table)
