"""Failed login attempt tracking for account lockout."""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class FailedLoginAttempt(Base):
    """
    Tracks failed login attempts per email for account lockout.

    After N failed attempts within the lockout window, the account
    is temporarily locked. Old records are cleaned up periodically.
    """

    __tablename__ = "failed_login_attempt"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, nullable=False, index=True)
    attempted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
