"""Add production FA-FR-008 wafer-level analysis persistence.

Revision ID: 009_fa_fr_008_wafer_analysis
Revises: 008_fa_fr_007_die_analysis
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "009_fa_fr_008_wafer_analysis"
down_revision: Union[str, None] = "008_fa_fr_007_die_analysis"
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
    if "wafer_analysis" not in tables:
        op.create_table(
            "wafer_analysis",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("wafer_result_id", sa.String(36), nullable=False, unique=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("classification_execution_id", sa.String(36), nullable=False),
            sa.Column("recurrence_analysis_id", sa.String(36), nullable=False),
            sa.Column("correlation_analysis_id", sa.String(36), nullable=False),
            sa.Column("die_analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("canonical_wafer_key", sa.String(64), nullable=False),
            sa.Column("total_dies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failing_dies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("yield_pct", sa.Float(), nullable=False, server_default="100"),
            sa.Column("failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("edge_failure_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("center_failure_rate", sa.Float(), nullable=False, server_default="0"),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("trend_status", sa.String(32), nullable=False),
            sa.Column("radial_distribution", sa.JSON(), nullable=False),
            sa.Column("lot_comparison", sa.JSON(), nullable=False),
            sa.Column("engineering_recommendation", sa.Text(), nullable=False, server_default=""),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "analysis_id",
                "canonical_wafer_key",
                name="uq_wafer_analysis_canonical",
            ),
        )
    for column in (
        "wafer_result_id",
        "analysis_id",
        "dataset_id",
        "upload_id",
        "detection_execution_id",
        "computation_id",
        "classification_execution_id",
        "recurrence_analysis_id",
        "correlation_analysis_id",
        "die_analysis_id",
        "lot_id",
        "wafer_id",
        "canonical_wafer_key",
        "severity",
        "trend_status",
    ):
        _index("wafer_analysis", column)

    definitions = {
        "wafer_statistics": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("scope_type", sa.String(32), nullable=False),
            sa.Column("scope_key", sa.String(512), nullable=False),
            sa.Column("total_wafers", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failing_wafers", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_dies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failing_dies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mean_yield_pct", sa.Float(), nullable=False, server_default="100"),
            sa.Column("mean_failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("mean_health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("mean_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("hotspot_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "wafer_hotspots": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("hotspot_id", sa.String(36), nullable=False, unique=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("wafer_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("center_x", sa.Float(), nullable=True),
            sa.Column("center_y", sa.Float(), nullable=True),
            sa.Column("radius", sa.Float(), nullable=False, server_default="0"),
            sa.Column("die_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failure_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("member_die_ids", sa.JSON(), nullable=False),
            sa.Column("density_grid", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "wafer_health_scores": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("wafer_result_id", sa.String(36), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("contributing_factors", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "wafer_yield_metrics": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("wafer_result_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("yield_pct", sa.Float(), nullable=False, server_default="100"),
            sa.Column("historical_yield_pct", sa.Float(), nullable=True),
            sa.Column("yield_delta", sa.Float(), nullable=True),
            sa.Column("trend_status", sa.String(32), nullable=False),
            sa.Column("lot_yield_pct", sa.Float(), nullable=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "wafer_analysis_history": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("wafer_result_id", sa.String(36), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("yield_pct", sa.Float(), nullable=False, server_default="100"),
            sa.Column("failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_execution_ids", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "wafer_audit_logs": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("source_die_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("wafer_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failing_wafer_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("hotspot_count", sa.Integer(), nullable=False, server_default="0"),
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
        "wafer_statistics": ("analysis_id", "scope_type", "scope_key"),
        "wafer_hotspots": ("hotspot_id", "analysis_id", "lot_id", "wafer_id", "severity"),
        "wafer_health_scores": (
            "wafer_result_id",
            "analysis_id",
            "lot_id",
            "wafer_id",
            "severity",
        ),
        "wafer_yield_metrics": (
            "analysis_id",
            "wafer_result_id",
            "lot_id",
            "wafer_id",
            "trend_status",
        ),
        "wafer_analysis_history": (
            "wafer_result_id",
            "analysis_id",
            "lot_id",
            "wafer_id",
        ),
        "wafer_audit_logs": ("analysis_id", "dataset_id", "upload_id", "status"),
    }
    tables = set(inspect(op.get_bind()).get_table_names())
    for name, columns in definitions.items():
        if name not in tables:
            op.create_table(name, *columns)
        for column in indexes[name]:
            _index(name, column)

    # Defensive: some local DBs may have skipped the FA-FR-006 widening of the shared
    # engineering_recommendations table; ensure correlation_id + source_module exist.
    if "engineering_recommendations" in tables:
        recommendation_columns = {
            item["name"]
            for item in inspect(op.get_bind()).get_columns("engineering_recommendations")
        }
        if "correlation_id" not in recommendation_columns:
            op.add_column(
                "engineering_recommendations",
                sa.Column("correlation_id", sa.String(36), nullable=True),
            )
            _index("engineering_recommendations", "correlation_id")
        if "source_module" not in recommendation_columns:
            op.add_column(
                "engineering_recommendations",
                sa.Column(
                    "source_module",
                    sa.String(32),
                    nullable=False,
                    server_default="FA-FR-005",
                ),
            )
            _index("engineering_recommendations", "source_module")
        # Production FA-FR-006/007/008 recommendations can be independent of recurrence rows.
        if "recurrence_id" in recommendation_columns:
            op.alter_column("engineering_recommendations", "recurrence_id", nullable=True)


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "engineering_recommendations" in tables:
        columns = {
            item["name"]
            for item in inspect(op.get_bind()).get_columns("engineering_recommendations")
        }
        if "source_module" in columns:
            op.drop_column("engineering_recommendations", "source_module")
        if "correlation_id" in columns:
            op.drop_column("engineering_recommendations", "correlation_id")
        if "recurrence_id" in columns:
            op.alter_column("engineering_recommendations", "recurrence_id", nullable=False)
    for name in (
        "wafer_audit_logs",
        "wafer_analysis_history",
        "wafer_yield_metrics",
        "wafer_health_scores",
        "wafer_hotspots",
        "wafer_statistics",
        "wafer_analysis",
    ):
        if name in tables:
            op.drop_table(name)
