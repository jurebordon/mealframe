"""Onboarding state model for AI-powered setup wizard (ADR-015)."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..database import Base


class OnboardingState(Base):
    """
    Persists onboarding wizard state for resume capability.

    One active onboarding per user (enforced via partial unique index in migration).
    Stores intake answers, AI-generated setup, chat history, and imported meals as JSONB.
    """
    __tablename__ = "onboarding_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Text, nullable=False, default="intake")  # CHECK constraint in migration
    intake_substep = Column(Integer, default=1)  # 1-6 within intake questionnaire
    intake_answers = Column(JSONB, nullable=False, default=dict)
    generated_setup = Column(JSONB, nullable=False, default=dict)
    chat_messages = Column(JSONB, nullable=False, default=list)
    tool_log = Column(JSONB, nullable=False, default=list)
    imported_meals = Column(JSONB, nullable=False, default=list)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")

    def __repr__(self):
        return f"<OnboardingState(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
