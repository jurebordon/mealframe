"""Add landing_pageview table for analytics.

Revision ID: 20260225_landing_pageview
Revises: 20260223_completion_statuses
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260225_landing_pageview"
down_revision = "20260223_completion_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "landing_pageview",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("page_url", sa.Text(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_landing_pageview_created_at",
        "landing_pageview",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_landing_pageview_created_at", "landing_pageview")
    op.drop_table("landing_pageview")
