"""User model for authentication and multi-user support."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    """
    User account for authentication.

    Supports email/password and Google OAuth login.
    Password hash is nullable for OAuth-only users.
    """

    __tablename__ = "user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=True)  # NULL for Google OAuth-only users
    email_verified = Column(Boolean, default=True, nullable=False)  # TODO: set to False when email verification is implemented
    is_active = Column(Boolean, default=True, nullable=False)
    auth_provider = Column(Text, default="email", nullable=False)  # "email" or "google"
    google_sub = Column(Text, unique=True, nullable=True)  # Google subject ID
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
