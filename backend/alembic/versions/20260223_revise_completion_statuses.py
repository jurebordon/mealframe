"""Revise completion statuses per ADR-012.

Rename: adjusted -> equivalent, replaced -> deviated
Add: actual_meal_id FK column
Update: CHECK constraint

Revision ID: 20260223_completion_statuses
Revises: 20260223_manual_override
Create Date: 2026-02-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260223_completion_statuses"
down_revision = "20260223_manual_override"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Rename existing status values in data
    op.execute(
        "UPDATE weekly_plan_slot SET completion_status = 'equivalent' WHERE completion_status = 'adjusted'"
    )
    op.execute(
        "UPDATE weekly_plan_slot SET completion_status = 'deviated' WHERE completion_status = 'replaced'"
    )

    # 2. Drop old CHECK constraint and add new one
    op.drop_constraint("ck_weekly_plan_slot_status", "weekly_plan_slot", type_="check")
    op.create_check_constraint(
        "ck_weekly_plan_slot_status",
        "weekly_plan_slot",
        "completion_status IS NULL OR completion_status IN ('followed', 'equivalent', 'skipped', 'deviated', 'social')",
    )

    # 3. Add actual_meal_id FK column
    op.add_column(
        "weekly_plan_slot",
        sa.Column(
            "actual_meal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meal.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove actual_meal_id column
    op.drop_column("weekly_plan_slot", "actual_meal_id")

    # Revert CHECK constraint
    op.drop_constraint("ck_weekly_plan_slot_status", "weekly_plan_slot", type_="check")
    op.create_check_constraint(
        "ck_weekly_plan_slot_status",
        "weekly_plan_slot",
        "completion_status IS NULL OR completion_status IN ('followed', 'adjusted', 'skipped', 'replaced', 'social')",
    )

    # Revert status values
    op.execute(
        "UPDATE weekly_plan_slot SET completion_status = 'adjusted' WHERE completion_status = 'equivalent'"
    )
    op.execute(
        "UPDATE weekly_plan_slot SET completion_status = 'replaced' WHERE completion_status = 'deviated'"
    )
