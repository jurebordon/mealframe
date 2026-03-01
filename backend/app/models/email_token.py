"""Email token model for verification and password reset flows."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class EmailToken(Base):
    """
    Time-limited token for email verification and password reset.

    Token types:
    - "verification": 24-hour expiry, verifies user email
    - "password_reset": 1-hour expiry, allows password change

    Tokens are single-use: marked as used after successful consumption.
    The raw token is sent to the user; only the hash is stored.
    """

    __tablename__ = "email_token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(Text, unique=True, nullable=False)
    token_type = Column(Text, nullable=False)  # "verification" or "password_reset"
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
