"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("mmsi", sa.Integer(), nullable=False),
        sa.Column("vessel_name", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_positions_timestamp", "timestamp"),
        sa.Index("ix_positions_mmsi", "mmsi"),
    )
    op.create_table(
        "metadata",
        sa.Column("mmsi", sa.Integer(), nullable=False),
        sa.Column("imo", sa.Integer(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("mmsi"),
    )


def downgrade() -> None:
    op.drop_table("metadata")
    op.drop_table("positions")