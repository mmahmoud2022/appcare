"""Align doctor schedule schema with new models

Revision ID: f3a2b1c4d5e6
Revises: f2b3c4d5e6a7
Create Date: 2025-11-07 15:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3a2b1c4d5e6"
down_revision: Union[str, Sequence[str], None] = "f2b3c4d5e6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # doctor_availabilities now becomes doctor_schedule to reflect recurring entries
    op.rename_table("doctor_availabilities", "doctor_schedule")

    # Rename indexes to reflect new table name
    op.execute(
        "ALTER INDEX IF EXISTS ix_doctor_availabilities_day_of_week RENAME TO ix_doctor_schedule_day_of_week"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_doctor_availabilities_doctor_id RENAME TO ix_doctor_schedule_doctor_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_doctor_availabilities_id RENAME TO ix_doctor_schedule_id"
    )

    # Extend schedule table with slot/break details and optional location
    op.add_column(
        "doctor_schedule",
        sa.Column("slot_duration", sa.Integer(), nullable=True),
    )
    op.add_column(
        "doctor_schedule",
        sa.Column("break_duration", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "doctor_schedule",
        sa.Column("location", sa.String(length=255), nullable=True),
    )

    # Remove legacy availability flag which is no longer used in recurring schedules
    op.drop_column("doctor_schedule", "is_available")

    # Ensure existing rows have a slot duration; default to 30 minutes when missing
    op.execute("UPDATE doctor_schedule SET slot_duration = 30 WHERE slot_duration IS NULL")
    op.alter_column(
        "doctor_schedule",
        "slot_duration",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Appointments now relate to schedule entries directly
    op.add_column(
        "appointments",
        sa.Column("schedule_entry_id", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE appointments SET schedule_entry_id = availability_id")
    op.create_foreign_key(
        "appointments_schedule_entry_id_fkey",
        "appointments",
        "doctor_schedule",
        ["schedule_entry_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_appointments_schedule_entry_id", "appointments", ["schedule_entry_id"])

    # Drop the old availability pointer
    op.drop_column("appointments", "availability_id")

    # Dedicated table for ad-hoc blocked slots
    op.create_table(
        "doctor_blocked_slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_doctor_blocked_slots_doctor_id", "doctor_blocked_slots", ["doctor_id"])
    op.create_index("ix_doctor_blocked_slots_start_datetime", "doctor_blocked_slots", ["start_datetime"])
    op.create_index("ix_doctor_blocked_slots_end_datetime", "doctor_blocked_slots", ["end_datetime"])


def downgrade() -> None:
    op.drop_index("ix_doctor_blocked_slots_end_datetime", table_name="doctor_blocked_slots")
    op.drop_index("ix_doctor_blocked_slots_start_datetime", table_name="doctor_blocked_slots")
    op.drop_index("ix_doctor_blocked_slots_doctor_id", table_name="doctor_blocked_slots")
    op.drop_table("doctor_blocked_slots")

    op.add_column(
        "appointments",
        sa.Column("availability_id", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE appointments SET availability_id = schedule_entry_id")
    op.drop_index("ix_appointments_schedule_entry_id", table_name="appointments")
    op.drop_constraint("appointments_schedule_entry_id_fkey", "appointments", type_="foreignkey")
    op.drop_column("appointments", "schedule_entry_id")

    op.alter_column(
        "doctor_schedule",
        "slot_duration",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.execute("UPDATE doctor_schedule SET slot_duration = NULL")
    op.add_column(
        "doctor_schedule",
        sa.Column("is_available", sa.Boolean(), nullable=True, server_default=sa.text("false")),
    )
    op.drop_column("doctor_schedule", "location")
    op.drop_column("doctor_schedule", "break_duration")
    op.drop_column("doctor_schedule", "slot_duration")

    op.rename_table("doctor_schedule", "doctor_availabilities")
    op.execute(
        "ALTER INDEX IF EXISTS ix_doctor_schedule_day_of_week RENAME TO ix_doctor_availabilities_day_of_week"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_doctor_schedule_doctor_id RENAME TO ix_doctor_availabilities_doctor_id"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_doctor_schedule_id RENAME TO ix_doctor_availabilities_id"
    )
    op.create_foreign_key(
        "appointments_availability_id_fkey",
        "appointments",
        "doctor_availabilities",
        ["availability_id"],
        ["id"],
        ondelete="SET NULL",
    )
