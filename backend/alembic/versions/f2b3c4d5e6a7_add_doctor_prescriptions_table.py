"""add_doctor_prescriptions_table

Revision ID: f2b3c4d5e6a7
Revises: e839784a8e16
Create Date: 2025-11-07 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f2b3c4d5e6a7"
down_revision: Union[str, None] = "e839784a8e16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PRESCRIPTION_STATUS_ENUM_NAME = "prescriptionstatusenum"
PRESCRIPTION_STATUS_VALUES = ("issued", "cancelled", "expired")


def upgrade() -> None:
    # Create the enum type for prescription status if it does not already exist
    prescription_status_enum = postgresql.ENUM(
        *PRESCRIPTION_STATUS_VALUES,
        name=PRESCRIPTION_STATUS_ENUM_NAME
    )
    prescription_status_enum.create(op.get_bind(), checkfirst=True)

    # Create doctor_prescriptions table
    op.create_table(
        "doctor_prescriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("prescription_number", sa.String(length=50), nullable=False),
        sa.Column("medications", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(*PRESCRIPTION_STATUS_VALUES, name=PRESCRIPTION_STATUS_ENUM_NAME, create_type=False), nullable=False, server_default=PRESCRIPTION_STATUS_VALUES[0]),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id")
    )

    # Indexes and constraints
    op.create_index("ix_doctor_prescriptions_id", "doctor_prescriptions", ["id"], unique=False)
    op.create_index("ix_doctor_prescriptions_doctor_id", "doctor_prescriptions", ["doctor_id"], unique=False)
    op.create_index("ix_doctor_prescriptions_patient_id", "doctor_prescriptions", ["patient_id"], unique=False)
    op.create_index("ix_doctor_prescriptions_appointment_id", "doctor_prescriptions", ["appointment_id"], unique=False)
    op.create_index("ix_doctor_prescriptions_prescription_number", "doctor_prescriptions", ["prescription_number"], unique=True)
    op.create_index("ix_doctor_prescriptions_status", "doctor_prescriptions", ["status"], unique=False)
    op.create_index("ix_doctor_prescriptions_issued_at", "doctor_prescriptions", ["issued_at"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_doctor_prescriptions_issued_at", table_name="doctor_prescriptions")
    op.drop_index("ix_doctor_prescriptions_status", table_name="doctor_prescriptions")
    op.drop_index("ix_doctor_prescriptions_prescription_number", table_name="doctor_prescriptions")
    op.drop_index("ix_doctor_prescriptions_appointment_id", table_name="doctor_prescriptions")
    op.drop_index("ix_doctor_prescriptions_patient_id", table_name="doctor_prescriptions")
    op.drop_index("ix_doctor_prescriptions_doctor_id", table_name="doctor_prescriptions")
    op.drop_index("ix_doctor_prescriptions_id", table_name="doctor_prescriptions")

    # Drop table
    op.drop_table("doctor_prescriptions")

    # Drop enum type
    prescription_status_enum = postgresql.ENUM(
        *PRESCRIPTION_STATUS_VALUES,
        name=PRESCRIPTION_STATUS_ENUM_NAME
    )
    prescription_status_enum.drop(op.get_bind(), checkfirst=True)
