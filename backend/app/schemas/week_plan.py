"""Pydantic schemas for WeekPlan and WeekPlanDay entities."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseSchema
from .common import Weekday, WEEKDAY_NAMES
from .day_template import DayTemplateCompact


class WeekPlanDayBase(BaseSchema):
    """Base fields for a day mapping within a week plan."""

    weekday: Weekday = Field(description="Weekday (0=Monday, 6=Sunday)")
    day_template_id: UUID = Field(description="Template to use for this day")


class WeekPlanDayCreate(WeekPlanDayBase):
    """Schema for creating a day mapping when creating/updating a week plan."""

    pass


class WeekPlanDayResponse(BaseSchema):
    """Day mapping response with expanded template info."""

    id: UUID
    weekday: int
    weekday_name: str = Field(description="Human-readable weekday name")
    day_template: DayTemplateCompact

    @classmethod
    def from_orm_with_name(cls, obj) -> "WeekPlanDayResponse":
        """Create response from ORM object, adding weekday name."""
        return cls(
            id=obj.id,
            weekday=obj.weekday,
            weekday_name=WEEKDAY_NAMES.get(obj.weekday, "Unknown"),
            day_template=DayTemplateCompact.model_validate(obj.day_template),
        )


class WeekPlanBase(BaseSchema):
    """Base fields for WeekPlan - shared between create/update."""

    name: str = Field(min_length=1, max_length=255, description="Display name")
    is_default: bool = Field(
        default=False, description="Whether this is the default week plan"
    )


class WeekPlanCreate(WeekPlanBase):
    """Schema for creating a new WeekPlan with day mappings."""

    days: list[WeekPlanDayCreate] = Field(
        default_factory=list,
        description="Day-to-template mappings (one per weekday)",
    )


class WeekPlanUpdate(BaseSchema):
    """Schema for updating a WeekPlan - all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    is_default: bool | None = None
    days: list[WeekPlanDayCreate] | None = Field(
        default=None,
        description="Replace all day mappings with this list",
    )


class WeekPlanResponse(WeekPlanBase):
    """Full WeekPlan response with day mappings."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    days: list[WeekPlanDayResponse] = Field(
        default_factory=list, description="Day-to-template mappings"
    )


class WeekPlanCompact(BaseSchema):
    """Compact WeekPlan for embedding in other responses."""

    id: UUID
    name: str


class WeekPlanListItem(BaseSchema):
    """WeekPlan item for list views."""

    id: UUID
    name: str
    is_default: bool
    day_count: int = Field(description="Number of days with templates assigned")
