"""Add sugar_g, saturated_fat_g, fiber_g to meal

Revision ID: 20260206_nutrients
Revises: 1454edda6380
Create Date: 2026-02-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260206_nutrients'
down_revision = '1454edda6380'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('meal', sa.Column('sugar_g', sa.Numeric(precision=6, scale=1), nullable=True))
    op.add_column('meal', sa.Column('saturated_fat_g', sa.Numeric(precision=6, scale=1), nullable=True))
    op.add_column('meal', sa.Column('fiber_g', sa.Numeric(precision=6, scale=1), nullable=True))


def downgrade() -> None:
    op.drop_column('meal', 'fiber_g')
    op.drop_column('meal', 'saturated_fat_g')
    op.drop_column('meal', 'sugar_g')
