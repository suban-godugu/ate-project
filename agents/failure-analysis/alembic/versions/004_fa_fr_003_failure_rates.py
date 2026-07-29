"""FA-FR-003 production failure-rate computation schema.

Revision ID: 004_fa_fr_003_failure_rates
Revises: 003_fa_fr_002_pattern_detection
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "004_fa_fr_003_failure_rates"
down_revision: Union[str, None] = "003_fa_fr_002_pattern_detection"
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
    if "failure_rates" not in existing:
        op.create_table(
            "failure_rates",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("detected_pattern_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("aggregation_level", sa.String(32), nullable=False),
            sa.Column("aggregation_key", sa.String(512), nullable=False),
            sa.Column("formula_version", sa.String(64), nullable=False),
            sa.Column("total_tests", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("pass_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("fail_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("failure_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("failure_density", sa.Float(), nullable=False, server_default="0"),
            sa.Column("pattern_frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("moving_average", sa.Float()),
            sa.Column("baseline_percentage", sa.Float()),
            sa.Column("historical_delta", sa.Float()),
            sa.Column("trend_status", sa.String(32), nullable=False, server_default="insufficient_data"),
            sa.Column("threshold_status", sa.String(32), nullable=False, server_default="within_limit"),
            sa.Column("threshold_value", sa.Float()),
            sa.Column("severity_level", sa.String(32), nullable=False, server_default="low"),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "computation_id",
                "pattern_id",
                "aggregation_level",
                "aggregation_key",
                name="uq_failure_rate_computation_scope",
            ),
        )
    for column in (
        "computation_id", "dataset_id", "upload_id", "detection_execution_id",
        "detected_pattern_id", "pattern_id", "aggregation_level", "aggregation_key",
    ):
        _index("failure_rates", f"ix_failure_rates_{column}", [column])

    if "failure_statistics" not in existing:
        op.create_table(
            "failure_statistics",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("aggregation_level", sa.String(32), nullable=False),
            sa.Column("metric_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mean_failure_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("median_failure_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("std_dev", sa.Float(), nullable=False, server_default="0"),
            sa.Column("minimum", sa.Float(), nullable=False, server_default="0"),
            sa.Column("maximum", sa.Float(), nullable=False, server_default="0"),
            sa.Column("total_tests", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("total_failures", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _index("failure_statistics", "ix_failure_statistics_computation_id", ["computation_id"])
    _index("failure_statistics", "ix_failure_statistics_aggregation_level", ["aggregation_level"])

    if "historical_failure_rates" not in existing:
        op.create_table(
            "historical_failure_rates",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("failure_rate_id", sa.String(36), sa.ForeignKey("failure_rates.id", ondelete="CASCADE"), nullable=False),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("aggregation_level", sa.String(32), nullable=False),
            sa.Column("aggregation_key", sa.String(512), nullable=False),
            sa.Column("failure_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("baseline_percentage", sa.Float()),
            sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_computation_ids", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("failure_rate_id", "computation_id", "pattern_id", "aggregation_level", "aggregation_key"):
        _index("historical_failure_rates", f"ix_historical_failure_rates_{column}", [column])

    if "trend_analysis" not in existing:
        op.create_table(
            "trend_analysis",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("failure_rate_id", sa.String(36), sa.ForeignKey("failure_rates.id", ondelete="CASCADE"), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("aggregation_level", sa.String(32), nullable=False),
            sa.Column("aggregation_key", sa.String(512), nullable=False),
            sa.Column("trend_direction", sa.String(32), nullable=False),
            sa.Column("current_percentage", sa.Float(), nullable=False, server_default="0"),
            sa.Column("moving_average", sa.Float()),
            sa.Column("baseline_percentage", sa.Float()),
            sa.Column("absolute_change", sa.Float()),
            sa.Column("relative_change", sa.Float()),
            sa.Column("abnormal_increase", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("computation_id", "failure_rate_id", "pattern_id", "aggregation_level", "aggregation_key"):
        _index("trend_analysis", f"ix_trend_analysis_{column}", [column])

    if "threshold_configuration" not in existing:
        op.create_table(
            "threshold_configuration",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("configuration_key", sa.String(128), nullable=False),
            sa.Column("version", sa.String(64), nullable=False),
            sa.Column("pattern_id", sa.String(128)),
            sa.Column("aggregation_level", sa.String(32)),
            sa.Column("warning_percentage", sa.Float(), nullable=False),
            sa.Column("critical_percentage", sa.Float(), nullable=False),
            sa.Column("abnormal_delta_percentage", sa.Float(), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("effective_to", sa.DateTime(timezone=True)),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_by", sa.String(128)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("configuration_key", "version", name="uq_threshold_configuration_key_version"),
        )
    for column in ("configuration_key", "pattern_id", "aggregation_level", "enabled"):
        _index("threshold_configuration", f"ix_threshold_configuration_{column}", [column])

    if "computation_history" not in existing:
        op.create_table(
            "computation_history",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("computation_id", sa.String(36), nullable=False, unique=True),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("formula_version", sa.String(64), nullable=False),
            sa.Column("aggregation_levels", sa.JSON(), nullable=False),
            sa.Column("window_size", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("source_record_count", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("metric_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("benchmark_metrics", sa.JSON(), nullable=False),
            sa.Column("errors", sa.JSON(), nullable=False),
            sa.Column("warnings", sa.JSON(), nullable=False),
            sa.Column("actor", sa.String(128)),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
        )
    for column in ("computation_id", "dataset_id", "upload_id", "detection_execution_id", "status"):
        _index("computation_history", f"ix_computation_history_{column}", [column])


def downgrade() -> None:
    for table in (
        "computation_history",
        "threshold_configuration",
        "trend_analysis",
        "historical_failure_rates",
        "failure_statistics",
        "failure_rates",
    ):
        if table in _tables():
            op.drop_table(table)
