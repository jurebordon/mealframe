"""Add nutrition_cache table for USDA + Open Food Facts lookup cache (ADR-015).

Revision ID: 20260414_nutrition_cache
Revises: 20260407_onboarding
Create Date: 2026-04-14
"""
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260414_nutrition_cache"
down_revision = "20260407_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nutrition_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("cache_type", sa.String(length=16), nullable=False),
        sa.Column("cache_key", sa.Text(), nullable=False),
        sa.Column("payload_json", JSONB(), nullable=False),
        sa.Column("normalized_macros", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_check_constraint(
        "ck_nutrition_cache_source",
        "nutrition_cache",
        "source IN ('usda', 'open_food_facts')",
    )
    op.create_check_constraint(
        "ck_nutrition_cache_type",
        "nutrition_cache",
        "cache_type IN ('search', 'item')",
    )

    op.create_index(
        "uq_nutrition_cache_lookup",
        "nutrition_cache",
        ["source", "cache_type", "cache_key"],
        unique=True,
    )
    op.create_index(
        "ix_nutrition_cache_expires_at",
        "nutrition_cache",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_nutrition_cache_expires_at", table_name="nutrition_cache")
    op.drop_index("uq_nutrition_cache_lookup", table_name="nutrition_cache")
    op.drop_constraint("ck_nutrition_cache_type", "nutrition_cache", type_="check")
    op.drop_constraint("ck_nutrition_cache_source", "nutrition_cache", type_="check")
    op.drop_table("nutrition_cache")
