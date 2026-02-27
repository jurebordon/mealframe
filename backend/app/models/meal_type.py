"""MealType model - defines functional eating slots."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class MealType(Base):
    """
    Defines functional eating slots (e.g., "Pre-Workout Snack").

    A meal type represents a category of meals that serve a specific purpose
    or occur at a specific time. Meals can be assigned to multiple meal types.
    """
    __tablename__ = "meal_type"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_meal_type_user_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(Text), default=list, server_default='{}')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="meal_types")
    meals = relationship("Meal", secondary="meal_to_meal_type", back_populates="meal_types")
    day_template_slots = relationship("DayTemplateSlot", back_populates="meal_type")
    round_robin_state = relationship("RoundRobinState", back_populates="meal_type", uselist=False)

    def __repr__(self):
        return f"<MealType(id={self.id}, name='{self.name}')>"
