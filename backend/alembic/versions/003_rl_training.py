"""RL training metrics on recommendations

Revision ID: 003_rl_training
Revises: 002_module_fact_rows
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_rl_training"
down_revision: Union[str, None] = "002_module_fact_rows"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("recommendations", sa.Column("reward_score", sa.Numeric(8, 4)))
    op.add_column("recommendations", sa.Column("approval_rate", sa.Numeric(5, 2)))
    op.add_column("recommendations", sa.Column("rejection_rate", sa.Numeric(5, 2)))
    op.add_column("recommendations", sa.Column("application_rate", sa.Numeric(5, 2)))
    op.add_column("recommendations", sa.Column("feedback_count", sa.Integer(), server_default="0"))
    op.add_column("recommendations", sa.Column("last_trained_at", sa.DateTime(timezone=True)))

    op.create_table(
        "recommendation_training_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("training_run", sa.String(64), nullable=False),
        sa.Column("reward", sa.Numeric(8, 4)),
        sa.Column("confidence_before", sa.Numeric(5, 2)),
        sa.Column("confidence_after", sa.Numeric(5, 2)),
        sa.Column("feedback_count", sa.Integer()),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_rec_training_rec",
        "recommendation_training_runs",
        ["recommendation_id", sa.text("processed_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_rec_training_rec", table_name="recommendation_training_runs")
    op.drop_table("recommendation_training_runs")
    op.drop_column("recommendations", "last_trained_at")
    op.drop_column("recommendations", "feedback_count")
    op.drop_column("recommendations", "application_rate")
    op.drop_column("recommendations", "rejection_rate")
    op.drop_column("recommendations", "approval_rate")
    op.drop_column("recommendations", "reward_score")
