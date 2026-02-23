"""Add is_manual_override to weekly_plan_slot

Revision ID: 20260223_manual_override
Revises: 20260218_soft_limits
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260223_manual_override'
down_revision = '20260218_soft_limits'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'weekly_plan_slot',
        sa.Column('is_manual_override', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('weekly_plan_slot', 'is_manual_override')
