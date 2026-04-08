"""Add onboarding_state table for AI-powered onboarding wizard (ADR-015).

Revision ID: 20260407_onboarding
Revises: 20260304_ai_capture
Create Date: 2026-04-07
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260407_onboarding"
down_revision = "20260304_ai_capture"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_state",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.Text(), nullable=False, server_default="intake"),
        sa.Column("intake_substep", sa.Integer(), server_default="1"),
        sa.Column("intake_answers", JSONB(), nullable=False, server_default="{}"),
        sa.Column("generated_setup", JSONB(), nullable=False, server_default="{}"),
        sa.Column("chat_messages", JSONB(), nullable=False, server_default="[]"),
        sa.Column("tool_log", JSONB(), nullable=False, server_default="[]"),
        sa.Column("imported_meals", JSONB(), nullable=False, server_default="[]"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Enforce valid status values
    op.create_check_constraint(
        "ck_onboarding_state_status",
        "onboarding_state",
        "status IN ('intake', 'generating', 'review', 'meal_import', 'applying', 'completed', 'abandoned')",
    )

    # Enforce at most one active onboarding per user
    op.create_index(
        "uq_onboarding_state_user_active",
        "onboarding_state",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('completed', 'abandoned')"),
    )


def downgrade() -> None:
    op.drop_index("uq_onboarding_state_user_active", table_name="onboarding_state")
    op.drop_constraint("ck_onboarding_state_status", "onboarding_state", type_="check")
    op.drop_table("onboarding_state")
