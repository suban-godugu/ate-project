"""module fact rows for dashboard seed data

Revision ID: 002_module_fact_rows
Revises: 001_initial
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_module_fact_rows"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "module_fact_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("module", sa.String(32), nullable=False),
        sa.Column("tab", sa.String(32)),
        sa.Column("row_data", postgresql.JSONB(), nullable=False),
        sa.Column("fab_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fabs.id")),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lots.id")),
        sa.Column("wafer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wafers.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_module_fact_rows_module",
        "module_fact_rows",
        ["module", "tab", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_module_fact_rows_module", table_name="module_fact_rows")
    op.drop_table("module_fact_rows")
