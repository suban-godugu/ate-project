"""Align production recurrence with FA-FR-005 and FA-FR-004 classification.

Revision ID: 006_fa_fr_005_recurrence
Revises: 005_fa_fr_004_recurrence
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "006_fa_fr_005_recurrence"
down_revision: Union[str, None] = "005_fa_fr_004_recurrence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table: str) -> set[str]:
    return {item["name"] for item in inspect(op.get_bind()).get_columns(table)}


def _indexes(table: str) -> set[str]:
    return {item["name"] for item in inspect(op.get_bind()).get_indexes(table)}


def _index(table: str, name: str, columns: list[str]) -> None:
    if name not in _indexes(table):
        op.create_index(name, table, columns)


def upgrade() -> None:
    columns = _columns("recurring_failures")
    additions = (
        ("classification_execution_id", sa.String(36), "legacy"),
        ("fault_type", sa.String(128), "Unknown Failure"),
        ("canonical_recurrence_key", sa.String(64), ""),
        ("recurrence_percentage", sa.Float(), "0"),
    )
    for name, column_type, default in additions:
        if name not in columns:
            op.add_column(
                "recurring_failures",
                sa.Column(name, column_type, nullable=False, server_default=default),
            )

    op.execute(
        """
        UPDATE recurring_failures
        SET canonical_recurrence_key = md5(pattern_id || '|' || signature_hash)
        WHERE canonical_recurrence_key = ''
        """
    )
    op.execute(
        """
        UPDATE recurring_failures
        SET recurrence_percentage = recurrence_frequency * 100.0
        WHERE recurrence_percentage = 0 AND recurrence_frequency <> 0
        """
    )

    unique_names = {
        item["name"]
        for item in inspect(op.get_bind()).get_unique_constraints("recurring_failures")
    }
    if "uq_recurring_failure_analysis_signature" in unique_names:
        op.drop_constraint(
            "uq_recurring_failure_analysis_signature",
            "recurring_failures",
            type_="unique",
        )
    if "uq_recurring_failure_analysis_canonical" not in unique_names:
        op.create_unique_constraint(
            "uq_recurring_failure_analysis_canonical",
            "recurring_failures",
            ["analysis_id", "canonical_recurrence_key"],
        )
    for column in (
        "classification_execution_id",
        "fault_type",
        "canonical_recurrence_key",
    ):
        _index("recurring_failures", f"ix_recurring_failures_{column}", [column])

    if "engineering_recommendations" not in inspect(op.get_bind()).get_table_names():
        op.create_table(
            "engineering_recommendations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("recommendation_id", sa.String(36), nullable=False, unique=True),
            sa.Column(
                "recurrence_id",
                sa.String(36),
                sa.ForeignKey("recurring_failures.recurrence_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("analysis_id", sa.String(36), nullable=False),
            sa.Column("pattern_id", sa.String(128), nullable=False),
            sa.Column("fault_type", sa.String(128), nullable=False),
            sa.Column("recommendation_code", sa.String(64), nullable=False),
            sa.Column("priority", sa.String(32), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
            sa.Column("evidence", sa.JSON(), nullable=False),
            sa.Column("config_version", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    for column in (
        "recommendation_id",
        "recurrence_id",
        "analysis_id",
        "pattern_id",
        "fault_type",
        "recommendation_code",
        "priority",
    ):
        _index(
            "engineering_recommendations",
            f"ix_engineering_recommendations_{column}",
            [column],
        )


def downgrade() -> None:
    tables = set(inspect(op.get_bind()).get_table_names())
    if "engineering_recommendations" in tables:
        op.drop_table("engineering_recommendations")
    unique_names = {
        item["name"]
        for item in inspect(op.get_bind()).get_unique_constraints("recurring_failures")
    }
    if "uq_recurring_failure_analysis_canonical" in unique_names:
        op.drop_constraint(
            "uq_recurring_failure_analysis_canonical",
            "recurring_failures",
            type_="unique",
        )
    if "uq_recurring_failure_analysis_signature" not in unique_names:
        op.create_unique_constraint(
            "uq_recurring_failure_analysis_signature",
            "recurring_failures",
            ["analysis_id", "pattern_id", "signature_hash"],
        )
    columns = _columns("recurring_failures")
    for column in (
        "recurrence_percentage",
        "canonical_recurrence_key",
        "fault_type",
        "classification_execution_id",
    ):
        if column in columns:
            op.drop_column("recurring_failures", column)
