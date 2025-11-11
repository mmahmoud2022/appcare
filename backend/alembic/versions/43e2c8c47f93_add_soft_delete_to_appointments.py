"""add_soft_delete_to_appointments

Revision ID: 43e2c8c47f93
Revises: f3a2b1c4d5e6
Create Date: 2025-11-10 03:26:42.384584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43e2c8c47f93'
down_revision: Union[str, None] = 'f3a2b1c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_deleted and deleted_at columns to appointments table
    op.add_column('appointments', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('appointments', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('appointments', sa.Column('deleted_by', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove soft delete columns
    op.drop_column('appointments', 'deleted_by')
    op.drop_column('appointments', 'deleted_at')
    op.drop_column('appointments', 'is_deleted')
