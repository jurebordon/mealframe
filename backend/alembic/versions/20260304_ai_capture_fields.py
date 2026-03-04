"""ai_capture_fields

Add AI capture fields to meal table and create openai_usage table (ADR-013).

Revision ID: 20260304_ai_capture
Revises: b09731906f17
Create Date: 2026-03-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "20260304_ai_capture"
down_revision = "b09731906f17"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI capture fields to meal table
    op.add_column("meal", sa.Column("source", sa.Text(), nullable=False, server_default="manual"))
    op.add_column("meal", sa.Column("confidence_score", sa.Numeric(3, 2), nullable=True))
    op.add_column("meal", sa.Column("image_path", sa.Text(), nullable=True))
    op.add_column("meal", sa.Column("ai_model_version", sa.Text(), nullable=True))

    # Create openai_usage table for cost tracking
    op.create_table(
        "openai_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("tokens_prompt", sa.Integer(), nullable=True),
        sa.Column("tokens_completion", sa.Integer(), nullable=True),
        sa.Column("cost_estimate_usd", sa.Numeric(8, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("openai_usage")
    op.drop_column("meal", "ai_model_version")
    op.drop_column("meal", "image_path")
    op.drop_column("meal", "confidence_score")
    op.drop_column("meal", "source")
