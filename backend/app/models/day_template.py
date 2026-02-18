"""DayTemplate models - defines reusable day patterns."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class DayTemplate(Base):
    """
    Defines reusable day patterns (e.g., "Morning Workout Workday").

    A day template is a collection of ordered meal type slots that define
    the structure of a day. Templates can be assigned to weekdays in a week plan.
    """
    __tablename__ = "day_template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False, unique=True)
    notes = Column(Text)
    max_calories_kcal = Column(Integer, nullable=True)
    max_protein_g = Column(Numeric(6, 1), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    slots = relationship("DayTemplateSlot", back_populates="day_template", cascade="all, delete-orphan", order_by="DayTemplateSlot.position")
    week_plan_days = relationship("WeekPlanDay", back_populates="day_template")
    weekly_plan_instance_days = relationship("WeeklyPlanInstanceDay", back_populates="day_template")

    def __repr__(self):
        return f"<DayTemplate(id={self.id}, name='{self.name}')>"


class DayTemplateSlot(Base):
    """
    Ordered meal type slots within a day template.

    Each slot defines a position in the day and the meal type that should
    be filled at that position. Positions are sequential (1, 2, 3, ...).
    """
    __tablename__ = "day_template_slot"
    __table_args__ = (
        UniqueConstraint("day_template_id", "position", name="uq_day_template_slot_position"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    day_template_id = Column(UUID(as_uuid=True), ForeignKey("day_template.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    meal_type_id = Column(UUID(as_uuid=True), ForeignKey("meal_type.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    day_template = relationship("DayTemplate", back_populates="slots")
    meal_type = relationship("MealType", back_populates="day_template_slots")

    def __repr__(self):
        return f"<DayTemplateSlot(id={self.id}, template={self.day_template_id}, position={self.position})>"
