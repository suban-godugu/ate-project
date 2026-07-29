"""Add production FA-FR-006 correlation persistence.

Revision ID: 007_fa_fr_006_correlation
Revises: 006_fa_fr_005_recurrence
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "007_fa_fr_006_correlation"
down_revision: Union[str, None] = "006_fa_fr_005_recurrence"
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
    if "failure_pattern_correlations" not in tables:
        op.create_table(
            "failure_pattern_correlations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("correlation_id", sa.String(36), nullable=False, unique=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("classification_execution_id", sa.String(36), nullable=False),
            sa.Column("recurrence_analysis_id", sa.String(36), nullable=False),
            sa.Column("recurrence_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("fault_type", sa.String(128), nullable=False),
            sa.Column("canonical_correlation_key", sa.String(64), nullable=False),
            sa.Column("correlated_failures", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("correlation_coefficient", sa.Float(), nullable=False, server_default="0"),
            sa.Column("correlation_strength", sa.String(32), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("p_value", sa.Float(), nullable=True),
            sa.Column("sample_size", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("trend_status", sa.String(32), nullable=False),
            sa.Column("hotspot_location", sa.JSON(), nullable=False),
            sa.Column("engineering_recommendation", sa.Text(), nullable=False, server_default=""),
            sa.Column("algorithm", sa.String(64), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("correlation_timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "analysis_id",
                "canonical_correlation_key",
                name="uq_correlation_analysis_canonical",
            ),
        )
    for column in (
        "correlation_id", "analysis_id", "dataset_id", "upload_id",
        "detection_execution_id", "computation_id", "classification_execution_id",
        "recurrence_analysis_id", "recurrence_id", "pattern_id", "fault_type",
        "canonical_correlation_key", "correlation_strength", "severity", "trend_status",
    ):
        _index("failure_pattern_correlations", column)

    definitions = {
        "correlation_statistics": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("scope_type", sa.String(32), nullable=False),
            sa.Column("scope_key", sa.String(512), nullable=False),
            sa.Column("correlation_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("strong_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mean_coefficient", sa.Float(), nullable=False, server_default="0"),
            sa.Column("mean_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "correlation_history": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("correlation_id", sa.String(36), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("fault_type", sa.String(128), nullable=False),
            sa.Column("coefficient", sa.Float(), nullable=False, server_default="0"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_execution_ids", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "correlation_trends": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("correlation_id", sa.String(36), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("fault_type", sa.String(128), nullable=False),
            sa.Column("trend_status", sa.String(32), nullable=False),
            sa.Column("current_coefficient", sa.Float(), nullable=False, server_default="0"),
            sa.Column("historical_coefficient", sa.Float(), nullable=False, server_default="0"),
            sa.Column("absolute_change", sa.Float(), nullable=False, server_default="0"),
            sa.Column("time_series", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "correlation_audit_logs": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("source_record_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("correlation_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("benchmark_metrics", sa.JSON(), nullable=False),
            sa.Column("upstream_execution_ids", sa.JSON(), nullable=False),
            sa.Column("errors", sa.JSON(), nullable=False),
            sa.Column("warnings", sa.JSON(), nullable=False),
            sa.Column("actor", sa.String(128), nullable=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        ],
    }
    indexes = {
        "correlation_statistics": ("analysis_id", "scope_type", "scope_key"),
        "correlation_history": ("correlation_id", "analysis_id", "pattern_id", "fault_type"),
        "correlation_trends": ("correlation_id", "analysis_id", "pattern_id", "fault_type", "trend_status"),
        "correlation_audit_logs": ("analysis_id", "dataset_id", "upload_id", "status"),
    }
    tables = set(inspect(op.get_bind()).get_table_names())
    for name, columns in definitions.items():
        if name not in tables:
            op.create_table(name, *columns)
        for column in indexes[name]:
            _index(name, column)

    recommendation_columns = {
        item["name"] for item in inspect(op.get_bind()).get_columns("engineering_recommendations")
    }
    if "correlation_id" not in recommendation_columns:
        op.add_column("engineering_recommendations", sa.Column("correlation_id", sa.String(36), nullable=True))
    if "source_module" not in recommendation_columns:
        op.add_column(
            "engineering_recommendations",
            sa.Column("source_module", sa.String(32), nullable=False, server_default="FA-FR-005"),
        )
    op.alter_column("engineering_recommendations", "recurrence_id", nullable=True)
    _index("engineering_recommendations", "correlation_id")
    _index("engineering_recommendations", "source_module")


def downgrade() -> None:
    columns = {
        item["name"] for item in inspect(op.get_bind()).get_columns("engineering_recommendations")
    }
    if "source_module" in columns:
        op.drop_column("engineering_recommendations", "source_module")
    if "correlation_id" in columns:
        op.drop_column("engineering_recommendations", "correlation_id")
    op.alter_column("engineering_recommendations", "recurrence_id", nullable=False)
    tables = set(inspect(op.get_bind()).get_table_names())
    for name in (
        "correlation_audit_logs",
        "correlation_trends",
        "correlation_history",
        "correlation_statistics",
        "failure_pattern_correlations",
    ):
        if name in tables:
            op.drop_table(name)
