"""Add production FA-FR-007 die-level analysis persistence.

Revision ID: 008_fa_fr_007_die_analysis
Revises: 007_fa_fr_006_correlation
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "008_fa_fr_007_die_analysis"
down_revision: Union[str, None] = "007_fa_fr_006_correlation"
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
    if "die_analysis" not in tables:
        op.create_table(
            "die_analysis",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("die_result_id", sa.String(36), nullable=False, unique=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("classification_execution_id", sa.String(36), nullable=False),
            sa.Column("recurrence_analysis_id", sa.String(36), nullable=False),
            sa.Column("correlation_analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("die_id", sa.String(128), nullable=False),
            sa.Column("canonical_die_key", sa.String(64), nullable=False),
            sa.Column("x", sa.Float(), nullable=True),
            sa.Column("y", sa.Float(), nullable=True),
            sa.Column("failure_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("total_tests", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("neighbor_failure_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_isolated", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_failing", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("trend_status", sa.String(32), nullable=False),
            sa.Column("dominant_fault_type", sa.String(128), nullable=False, server_default=""),
            sa.Column("dominant_pattern_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("hotspot_id", sa.String(36), nullable=True),
            sa.Column("cluster_id", sa.String(36), nullable=True),
            sa.Column("engineering_recommendation", sa.Text(), nullable=False, server_default=""),
            sa.Column("lot_comparison", sa.JSON(), nullable=False),
            sa.Column("wafer_comparison", sa.JSON(), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "analysis_id",
                "canonical_die_key",
                name="uq_die_analysis_canonical",
            ),
        )
    for column in (
        "die_result_id",
        "analysis_id",
        "dataset_id",
        "upload_id",
        "detection_execution_id",
        "computation_id",
        "classification_execution_id",
        "recurrence_analysis_id",
        "correlation_analysis_id",
        "lot_id",
        "wafer_id",
        "die_id",
        "canonical_die_key",
        "is_isolated",
        "is_failing",
        "severity",
        "trend_status",
        "dominant_fault_type",
        "dominant_pattern_id",
        "hotspot_id",
        "cluster_id",
    ):
        _index("die_analysis", column)

    definitions = {
        "die_failure_statistics": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("scope_type", sa.String(32), nullable=False),
            sa.Column("scope_key", sa.String(512), nullable=False),
            sa.Column("total_dies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failing_dies", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("isolated_failures", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mean_failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("mean_health_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("mean_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("hotspot_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cluster_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "die_hotspots": [
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
            sa.Column("coordinates", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "die_clusters": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("cluster_id", sa.String(36), nullable=False, unique=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("wafer_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("algorithm", sa.String(64), nullable=False, server_default="grid_union_find"),
            sa.Column("die_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failure_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("centroid_x", sa.Float(), nullable=True),
            sa.Column("centroid_y", sa.Float(), nullable=True),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("member_die_ids", sa.JSON(), nullable=False),
            sa.Column("coordinates", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "die_health_scores": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("die_result_id", sa.String(36), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("die_id", sa.String(128), nullable=False),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("severity", sa.String(32), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("contributing_factors", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "die_analysis_history": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("die_result_id", sa.String(36), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False),
            sa.Column("wafer_id", sa.String(128), nullable=False),
            sa.Column("die_id", sa.String(128), nullable=False),
            sa.Column("failure_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("health_score", sa.Float(), nullable=False, server_default="1"),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_execution_ids", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "die_audit_logs": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("source_record_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("die_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failing_die_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("hotspot_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("cluster_count", sa.Integer(), nullable=False, server_default="0"),
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
        "die_failure_statistics": ("analysis_id", "scope_type", "scope_key"),
        "die_hotspots": ("hotspot_id", "analysis_id", "lot_id", "wafer_id", "severity"),
        "die_clusters": ("cluster_id", "analysis_id", "lot_id", "wafer_id", "severity"),
        "die_health_scores": (
            "die_result_id",
            "analysis_id",
            "lot_id",
            "wafer_id",
            "die_id",
            "severity",
        ),
        "die_analysis_history": (
            "die_result_id",
            "analysis_id",
            "lot_id",
            "wafer_id",
            "die_id",
        ),
        "die_audit_logs": ("analysis_id", "dataset_id", "upload_id", "status"),
    }
    tables = set(inspect(op.get_bind()).get_table_names())
    for name, columns in definitions.items():
        if name not in tables:
            op.create_table(name, *columns)
        for column in indexes[name]:
            _index(name, column)


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    for name in (
        "die_audit_logs",
        "die_analysis_history",
        "die_health_scores",
        "die_clusters",
        "die_hotspots",
        "die_failure_statistics",
        "die_analysis",
    ):
        if name in tables:
            op.drop_table(name)
