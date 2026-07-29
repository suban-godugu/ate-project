"""Initial PostgreSQL schema for Failure Analysis Agent.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-07-14

Creates all ORM tables from ``backend.models``. Future schema changes should
use ``alembic revision --autogenerate``.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from backend import models  # noqa: F401
    from backend.database import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from backend import models  # noqa: F401
    from backend.database import Base

    Base.metadata.drop_all(bind=op.get_bind())
