"""OpenAI usage logging model for cost tracking (ADR-013)."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class OpenAIUsage(Base):
    """
    Logs each OpenAI API call for cost monitoring.

    Informational only — no enforcement or rate limiting in MVP.
    Enables per-user cost visibility and model performance tracking.
    """

    __tablename__ = "openai_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model = Column(Text, nullable=False)
    tokens_prompt = Column(Integer)
    tokens_completion = Column(Integer)
    cost_estimate_usd = Column(Numeric(8, 6))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
