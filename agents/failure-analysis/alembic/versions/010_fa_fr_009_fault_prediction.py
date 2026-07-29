"""Add production FA-FR-009 fault-type prediction persistence.

Revision ID: 010_fa_fr_009_fault_prediction
Revises: 009_fa_fr_008_wafer_analysis
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "010_fa_fr_009_fault_prediction"
down_revision: Union[str, None] = "009_fa_fr_008_wafer_analysis"
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
    if "fault_predictions" not in tables:
        op.create_table(
            "fault_predictions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("prediction_id", sa.String(36), nullable=False, unique=True),
            sa.Column("execution_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("detection_execution_id", sa.String(36), nullable=False),
            sa.Column("computation_id", sa.String(36), nullable=False),
            sa.Column("classification_execution_id", sa.String(36), nullable=False),
            sa.Column("recurrence_analysis_id", sa.String(36), nullable=False),
            sa.Column("correlation_analysis_id", sa.String(36), nullable=False),
            sa.Column("die_analysis_id", sa.String(36), nullable=False),
            sa.Column("wafer_analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("canonical_prediction_key", sa.String(64), nullable=False),
            sa.Column("predicted_fault_type", sa.String(128), nullable=False),
            sa.Column("alternative_fault_types", sa.JSON(), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("prediction_probability", sa.Float(), nullable=False, server_default="0"),
            sa.Column("supporting_evidence", sa.JSON(), nullable=False),
            sa.Column("engineering_explanation", sa.Text(), nullable=False, server_default=""),
            sa.Column("investigation_steps", sa.JSON(), nullable=False),
            sa.Column("model_version", sa.String(64), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint(
                "execution_id",
                "canonical_prediction_key",
                name="uq_fault_prediction_canonical",
            ),
        )
    for column in (
        "prediction_id",
        "execution_id",
        "dataset_id",
        "upload_id",
        "detection_execution_id",
        "computation_id",
        "classification_execution_id",
        "recurrence_analysis_id",
        "correlation_analysis_id",
        "die_analysis_id",
        "wafer_analysis_id",
        "pattern_id",
        "canonical_prediction_key",
        "predicted_fault_type",
        "model_version",
    ):
        _index("fault_predictions", column)

    definitions = {
        "prediction_history": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("prediction_id", sa.String(36), nullable=False),
            sa.Column("execution_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("predicted_fault_type", sa.String(128), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("prediction_probability", sa.Float(), nullable=False, server_default="0"),
            sa.Column("snapshot_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_execution_ids", sa.JSON(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "prediction_statistics": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("execution_id", sa.String(36), nullable=False),
            sa.Column("scope_type", sa.String(32), nullable=False),
            sa.Column("scope_key", sa.String(512), nullable=False),
            sa.Column("total_predictions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("high_confidence_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("mean_confidence", sa.Float(), nullable=False, server_default="0"),
            sa.Column("mean_probability", sa.Float(), nullable=False, server_default="0"),
            sa.Column("top_fault_type", sa.String(128), nullable=False, server_default=""),
            sa.Column("top1_accuracy", sa.Float(), nullable=True),
            sa.Column("top3_accuracy", sa.Float(), nullable=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "prediction_feedback": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("feedback_id", sa.String(36), nullable=False, unique=True),
            sa.Column("prediction_id", sa.String(36), nullable=False),
            sa.Column("execution_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("validated_fault_type", sa.String(128), nullable=False),
            sa.Column("feedback_status", sa.String(32), nullable=False),
            sa.Column("engineer_notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("learning_weight", sa.Float(), nullable=False, server_default="1"),
            sa.Column("actor", sa.String(128), nullable=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "prediction_models": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("model_id", sa.String(36), nullable=False, unique=True),
            sa.Column("model_version", sa.String(64), nullable=False, unique=True),
            sa.Column("model_type", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False),
            sa.Column("metrics", sa.JSON(), nullable=False),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        ],
        "prediction_audit_logs": [
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("execution_id", sa.String(36), nullable=False),
            sa.Column("dataset_id", sa.String(36), nullable=True),
            sa.Column("upload_id", sa.String(36), nullable=True),
            sa.Column("status", sa.String(32), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("model_version", sa.String(64), nullable=False),
            sa.Column("source_pattern_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("prediction_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("high_confidence_count", sa.Integer(), nullable=False, server_default="0"),
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
        "prediction_history": (
            "prediction_id",
            "execution_id",
            "pattern_id",
            "predicted_fault_type",
        ),
        "prediction_statistics": ("execution_id", "scope_type", "scope_key"),
        "prediction_feedback": (
            "feedback_id",
            "prediction_id",
            "execution_id",
            "pattern_id",
            "validated_fault_type",
            "feedback_status",
        ),
        "prediction_models": ("model_id", "model_version", "model_type", "status"),
        "prediction_audit_logs": (
            "execution_id",
            "dataset_id",
            "upload_id",
            "status",
            "model_version",
        ),
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
        "prediction_audit_logs",
        "prediction_models",
        "prediction_feedback",
        "prediction_statistics",
        "prediction_history",
        "fault_predictions",
    ):
        if name in tables:
            op.drop_table(name)
