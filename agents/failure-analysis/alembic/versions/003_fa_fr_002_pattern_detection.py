"""FA-FR-002 production pattern detection schema.

Revision ID: 003_fa_fr_002_pattern_detection
Revises: 002_fa_fr_001_ingestion
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "003_fa_fr_002_pattern_detection"
down_revision: Union[str, None] = "002_fa_fr_001_ingestion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tables() -> set[str]:
    return set(inspect(op.get_bind()).get_table_names())


def _columns(table: str) -> set[str]:
    return {c["name"] for c in inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {i["name"] for i in inspect(op.get_bind()).get_indexes(table)}


def _index(table: str, name: str, columns: list[str]) -> None:
    if name not in _indexes(table):
        op.create_index(name, table, columns)


def upgrade() -> None:
    existing = _tables()
    additions: list[tuple[str, sa.TypeEngine, bool, object | None]] = [
        ("dataset_id", sa.String(36), True, None),
        ("pattern_name", sa.String(256), False, ""),
        ("pattern_category", sa.String(128), False, "unknown"),
        ("pattern_frequency", sa.Float(), False, 0.0),
        ("detection_method", sa.String(64), False, "statistical"),
        ("severity_level", sa.String(32), False, "medium"),
        ("affected_devices", sa.JSON(), False, "[]"),
        ("affected_dies", sa.JSON(), False, "[]"),
        ("affected_wafers", sa.JSON(), False, "[]"),
        ("affected_lots", sa.JSON(), False, "[]"),
        ("engineering_explanation", sa.Text(), False, ""),
        ("source_signature", sa.String(512), False, ""),
        ("rule_id", sa.String(36), True, None),
        ("updated_at", sa.DateTime(timezone=True), True, None),
    ]
    if "detected_patterns" in existing:
        current = _columns("detected_patterns")
        for name, type_, nullable, default in additions:
            if name not in current:
                op.add_column(
                    "detected_patterns",
                    sa.Column(
                        name,
                        type_,
                        nullable=nullable,
                        server_default=None if default is None else sa.text(repr(default)),
                    ),
                )
        _index("detected_patterns", "ix_detected_patterns_dataset_id", ["dataset_id"])
        _index("detected_patterns", "ix_detected_patterns_source_signature", ["source_signature"])

    if "pattern_occurrences" not in existing:
        op.create_table(
            "pattern_occurrences",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("detected_pattern_id", sa.String(36), sa.ForeignKey("detected_patterns.id", ondelete="CASCADE"), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("source_record_id", sa.String(512), nullable=False),
            sa.Column("lot_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("wafer_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("die_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("device_id", sa.String(128), nullable=False, server_default=""),
            sa.Column("x", sa.Integer()),
            sa.Column("y", sa.Integer()),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("detected_pattern_id", "source_record_id", name="uq_pattern_occurrence_source"),
        )
    for column in ("detected_pattern_id", "analysis_id", "dataset_id", "upload_id", "lot_id", "wafer_id", "die_id", "device_id"):
        _index("pattern_occurrences", f"ix_pattern_occurrences_{column}", [column])

    if "pattern_statistics" not in existing:
        op.create_table(
            "pattern_statistics",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("detected_pattern_id", sa.String(36), sa.ForeignKey("detected_patterns.id", ondelete="CASCADE"), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("scope_type", sa.String(32), nullable=False),
            sa.Column("scope_key", sa.String(384), nullable=False),
            sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("frequency", sa.Float(), nullable=False, server_default="0"),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in ("detected_pattern_id", "analysis_id", "scope_type", "scope_key"):
        _index("pattern_statistics", f"ix_pattern_statistics_{column}", [column])

    if "pattern_confidence" not in existing:
        op.create_table(
            "pattern_confidence",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("detected_pattern_id", sa.String(36), sa.ForeignKey("detected_patterns.id", ondelete="CASCADE"), nullable=False),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("composite_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("rule_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("statistical_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("similarity_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("threshold", sa.Float(), nullable=False, server_default="0"),
            sa.Column("passed_threshold", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("breakdown", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _index("pattern_confidence", "ix_pattern_confidence_detected_pattern_id", ["detected_pattern_id"])
    _index("pattern_confidence", "ix_pattern_confidence_analysis_id", ["analysis_id"])

    if "detection_history" not in existing:
        op.create_table(
            "detection_history",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36)),
            sa.Column("upload_id", sa.String(36)),
            sa.Column("execution_status", sa.String(32), nullable=False),
            sa.Column("rule_set_version", sa.String(64), nullable=False, server_default=""),
            sa.Column("pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("source_record_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processing_ms", sa.Float(), nullable=False, server_default="0"),
            sa.Column("confidence_distribution", sa.JSON(), nullable=False),
            sa.Column("benchmark_metrics", sa.JSON(), nullable=False),
            sa.Column("errors", sa.JSON(), nullable=False),
            sa.Column("warnings", sa.JSON(), nullable=False),
            sa.Column("actor", sa.String(128)),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True)),
        )
    for column in ("analysis_id", "dataset_id", "upload_id", "execution_status"):
        _index("detection_history", f"ix_detection_history_{column}", [column])

    if "rule_library" not in existing:
        op.create_table(
            "rule_library",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("rule_key", sa.String(128), nullable=False),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("category", sa.String(128), nullable=False),
            sa.Column("version", sa.String(64), nullable=False),
            sa.Column("customer_id", sa.String(128)),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("severity_level", sa.String(32), nullable=False, server_default="medium"),
            sa.Column("confidence_weight", sa.Float(), nullable=False, server_default="1"),
            sa.Column("definition", sa.JSON(), nullable=False),
            sa.Column("explanation_template", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_by", sa.String(128)),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("rule_key", "version", name="uq_rule_library_key_version"),
        )
    for column in ("rule_key", "category", "customer_id", "enabled"):
        _index("rule_library", f"ix_rule_library_{column}", [column])


def downgrade() -> None:
    for table in ("rule_library", "detection_history", "pattern_confidence", "pattern_statistics", "pattern_occurrences"):
        if table in _tables():
            op.drop_table(table)
    if "detected_patterns" in _tables():
        for name, *_ in reversed([
            ("dataset_id",), ("pattern_name",), ("pattern_category",), ("pattern_frequency",),
            ("detection_method",), ("severity_level",), ("affected_devices",), ("affected_dies",),
            ("affected_wafers",), ("affected_lots",), ("engineering_explanation",),
            ("source_signature",), ("rule_id",), ("updated_at",),
        ]):
            if name in _columns("detected_patterns"):
                op.drop_column("detected_patterns", name)
