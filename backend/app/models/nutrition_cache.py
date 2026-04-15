"""Nutrition lookup cache model for USDA + Open Food Facts (ADR-015)."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from ..database import Base


class NutritionCache(Base):
    """
    Per-ingredient cache for external nutrition API lookups.

    Two cache types share this table:
    - ``search`` rows map a normalized query string to an external id (payload holds the
      search hit). ``normalized_macros`` is null.
    - ``item`` rows map an external id to the fully normalized macros + raw upstream payload.

    Rows are ignored past ``expires_at``. Uniqueness is enforced on
    ``(source, cache_type, cache_key)``.
    """
    __tablename__ = "nutrition_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source = Column(String(16), nullable=False)  # 'usda' | 'open_food_facts'
    cache_type = Column(String(16), nullable=False)  # 'search' | 'item'
    cache_key = Column(Text, nullable=False)
    payload_json = Column(JSONB, nullable=False)
    normalized_macros = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "source IN ('usda', 'open_food_facts')",
            name="ck_nutrition_cache_source",
        ),
        CheckConstraint(
            "cache_type IN ('search', 'item')",
            name="ck_nutrition_cache_type",
        ),
        Index(
            "uq_nutrition_cache_lookup",
            "source",
            "cache_type",
            "cache_key",
            unique=True,
        ),
        Index("ix_nutrition_cache_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<NutritionCache(source={self.source!r}, type={self.cache_type!r}, "
            f"key={self.cache_key!r})>"
        )
