"""WeeklyPlan models - generated instances of weeks with concrete meal assignments."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class WeeklyPlanInstance(Base):
    """
    Generated instance of a week.

    Created when user generates a new week. Contains a week_start_date (Monday)
    and references the week plan it was generated from. Each instance has
    multiple days with concrete meal assignments.
    """
    __tablename__ = "weekly_plan_instance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    week_plan_id = Column(UUID(as_uuid=True), ForeignKey("week_plan.id", ondelete="SET NULL"))
    week_start_date = Column(Date, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    week_plan = relationship("WeekPlan", back_populates="weekly_plan_instances")
    days = relationship("WeeklyPlanInstanceDay", back_populates="weekly_plan_instance", cascade="all, delete-orphan")
    slots = relationship("WeeklyPlanSlot", back_populates="weekly_plan_instance", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WeeklyPlanInstance(id={self.id}, week_start={self.week_start_date})>"


class WeeklyPlanInstanceDay(Base):
    """
    Tracks template used for each day in a weekly instance.

    Supports template switching - users can change the template for a day
    after generation. Also supports "no plan" overrides for exceptional days.
    """
    __tablename__ = "weekly_plan_instance_day"
    __table_args__ = (
        UniqueConstraint("weekly_plan_instance_id", "date", name="uq_weekly_plan_instance_day_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    weekly_plan_instance_id = Column(UUID(as_uuid=True), ForeignKey("weekly_plan_instance.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    day_template_id = Column(UUID(as_uuid=True), ForeignKey("day_template.id", ondelete="SET NULL"))
    is_override = Column(Boolean, default=False, nullable=False)
    override_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    weekly_plan_instance = relationship("WeeklyPlanInstance", back_populates="days")
    day_template = relationship("DayTemplate", back_populates="weekly_plan_instance_days")

    def __repr__(self):
        return f"<WeeklyPlanInstanceDay(id={self.id}, date={self.date}, is_override={self.is_override})>"


class WeeklyPlanSlot(Base):
    """
    Individual meal slots with assignments and completion tracking.

    Each slot represents one meal on one day, with a concrete meal assignment
    from round-robin generation. Tracks completion status and timestamp.
    """
    __tablename__ = "weekly_plan_slot"
    __table_args__ = (
        CheckConstraint(
            "completion_status IS NULL OR completion_status IN ('followed', 'equivalent', 'skipped', 'deviated', 'social')",
            name="ck_weekly_plan_slot_status"
        ),
        UniqueConstraint("weekly_plan_instance_id", "date", "position", name="uq_weekly_plan_slot_position"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    weekly_plan_instance_id = Column(UUID(as_uuid=True), ForeignKey("weekly_plan_instance.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    position = Column(Integer, nullable=False)
    meal_type_id = Column(UUID(as_uuid=True), ForeignKey("meal_type.id", ondelete="SET NULL"))
    meal_id = Column(UUID(as_uuid=True), ForeignKey("meal.id", ondelete="SET NULL"))
    is_adhoc = Column(Boolean, default=False, nullable=False, server_default="false")
    is_manual_override = Column(Boolean, default=False, nullable=False, server_default="false")
    completion_status = Column(Text)  # NULL or one of: followed, equivalent, skipped, deviated, social
    completed_at = Column(DateTime(timezone=True))
    actual_meal_id = Column(UUID(as_uuid=True), ForeignKey("meal.id", ondelete="SET NULL"))

    # Relationships
    weekly_plan_instance = relationship("WeeklyPlanInstance", back_populates="slots")
    meal_type = relationship("MealType")
    meal = relationship("Meal", foreign_keys=[meal_id], back_populates="weekly_plan_slots")
    actual_meal = relationship("Meal", foreign_keys=[actual_meal_id])

    # Create composite index for efficient querying by instance and date
    __table_args__ = (
        __table_args__[0],  # Keep the CheckConstraint
        __table_args__[1],  # Keep the UniqueConstraint
    )

    def __repr__(self):
        return f"<WeeklyPlanSlot(id={self.id}, date={self.date}, position={self.position}, status={self.completion_status})>"
