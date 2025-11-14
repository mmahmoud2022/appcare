"""Add meet_link to appointments for teleconsultation

Revision ID: g1h2i3j4k5l6
Revises: f3a2b1c4d5e6
Create Date: 2025-11-13 19:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "f3a2b1c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add meet_link column to appointments table for teleconsultation support"""
    op.add_column(
        "appointments",
        sa.Column("meet_link", sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    """Remove meet_link column from appointments table"""
    op.drop_column("appointments", "meet_link")