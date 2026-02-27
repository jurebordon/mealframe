"""WeekPlan models - defines default week structure."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class WeekPlan(Base):
    """
    Defines default week structure.

    A week plan maps day templates to weekdays. One plan can be marked as default,
    which is used when generating new weekly instances. Application-level enforcement
    ensures only one default exists (per user).
    """
    __tablename__ = "week_plan"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="week_plans")
    days = relationship("WeekPlanDay", back_populates="week_plan", cascade="all, delete-orphan", order_by="WeekPlanDay.weekday")
    weekly_plan_instances = relationship("WeeklyPlanInstance", back_populates="week_plan")

    def __repr__(self):
        return f"<WeekPlan(id={self.id}, name='{self.name}', is_default={self.is_default})>"


class WeekPlanDay(Base):
    """
    Maps day templates to weekdays within a week plan.

    Each weekday (0=Monday, 6=Sunday) can have one template assigned.
    The template defines which meal types will appear on that day.
    """
    __tablename__ = "week_plan_day"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_week_plan_day_weekday"),
        UniqueConstraint("week_plan_id", "weekday", name="uq_week_plan_day_weekday"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    week_plan_id = Column(UUID(as_uuid=True), ForeignKey("week_plan.id", ondelete="CASCADE"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    day_template_id = Column(UUID(as_uuid=True), ForeignKey("day_template.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    week_plan = relationship("WeekPlan", back_populates="days")
    day_template = relationship("DayTemplate", back_populates="week_plan_days")

    def __repr__(self):
        return f"<WeekPlanDay(id={self.id}, weekday={self.weekday}, template={self.day_template_id})>"
