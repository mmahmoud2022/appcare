"""add meet_link to appointments

Revision ID: 20251111_add_meet_link_to_appointments
Revises: 
Create Date: 2025-11-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251111_add_meet_link_to_appointments'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('appointments', sa.Column('meet_link', sa.String(length=500), nullable=True))


def downgrade():
    op.drop_column('appointments', 'meet_link')
