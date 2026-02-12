"""Add is_adhoc boolean to weekly_plan_slot

Revision ID: 20260212_adhoc
Revises: 20260206_nutrients
Create Date: 2026-02-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260212_adhoc'
down_revision = '20260206_nutrients'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'weekly_plan_slot',
        sa.Column('is_adhoc', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('weekly_plan_slot', 'is_adhoc')
