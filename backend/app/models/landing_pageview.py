"""Landing page pageview tracking model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class LandingPageview(Base):
    """Tracks pageviews on the landing/waitlist page."""

    __tablename__ = "landing_pageview"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    page_url = Column(Text, nullable=False)
    referrer = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(64), nullable=True)
    ip_hash = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_landing_pageview_created_at", "created_at"),
    )
