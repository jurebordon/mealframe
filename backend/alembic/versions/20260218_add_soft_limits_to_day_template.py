"""Add max_calories_kcal and max_protein_g to day_template

Revision ID: 20260218_soft_limits
Revises: 20260212_adhoc
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260218_soft_limits'
down_revision = '20260212_adhoc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'day_template',
        sa.Column('max_calories_kcal', sa.Integer(), nullable=True),
    )
    op.add_column(
        'day_template',
        sa.Column('max_protein_g', sa.Numeric(6, 1), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('day_template', 'max_protein_g')
    op.drop_column('day_template', 'max_calories_kcal')
