"""Meal model - defines specific foods with portions and macros."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Meal(Base):
    """
    Defines specific foods with exact portions and macros.

    Each meal must have a portion description (invariant) and can optionally
    include nutritional information. Meals can be assigned to multiple meal types.
    """
    __tablename__ = "meal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False, index=True)
    portion_description = Column(Text, nullable=False)  # MANDATORY - invariant
    calories_kcal = Column(Integer)
    protein_g = Column(Numeric(6, 1))
    carbs_g = Column(Numeric(6, 1))
    sugar_g = Column(Numeric(6, 1))
    fat_g = Column(Numeric(6, 1))
    saturated_fat_g = Column(Numeric(6, 1))
    fiber_g = Column(Numeric(6, 1))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    meal_types = relationship("MealType", secondary="meal_to_meal_type", back_populates="meals")
    weekly_plan_slots = relationship("WeeklyPlanSlot", foreign_keys="[WeeklyPlanSlot.meal_id]", back_populates="meal")

    def __repr__(self):
        return f"<Meal(id={self.id}, name='{self.name}', portion='{self.portion_description}')>"
