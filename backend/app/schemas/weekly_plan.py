"""Pydantic schemas for WeeklyPlanInstance, WeeklyPlanInstanceDay, and WeeklyPlanSlot entities."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from .base import BaseSchema
from .common import CompletionStatus, WEEKDAY_NAMES
from .day_template import DayTemplateCompact
from .meal import MealCompact
from .meal_type import MealTypeCompact
from .week_plan import WeekPlanCompact


class WeeklyPlanSlotBase(BaseSchema):
    """Base slot representation in a weekly plan."""

    id: UUID
    position: int
    meal_type: MealTypeCompact | None = None
    meal: MealCompact | None = None
    completion_status: CompletionStatus | None = None
    completed_at: datetime | None = None
    is_adhoc: bool = False
    is_manual_override: bool = False
    actual_meal: MealCompact | None = None


class WeeklyPlanSlotResponse(WeeklyPlanSlotBase):
    """Slot response for general use."""

    pass


class WeeklyPlanSlotWithNext(WeeklyPlanSlotBase):
    """Slot response with is_next computed field for Today view.

    Per Tech Spec GET /today, is_next indicates the first slot with null completion_status.
    """

    is_next: bool = Field(
        default=False,
        description="True if this is the next meal to complete",
    )


class CompletionSummary(BaseSchema):
    """Summary of completion status for a day."""

    completed: int = Field(description="Number of completed slots")
    total: int = Field(description="Total number of slots")


class WeeklyPlanInstanceDayBase(BaseSchema):
    """Base day representation in a weekly instance."""

    date: date
    weekday: str = Field(description="Human-readable weekday name")
    template: DayTemplateCompact | None = None
    is_override: bool = False
    override_reason: str | None = None


class WeeklyPlanInstanceDayResponse(WeeklyPlanInstanceDayBase):
    """Day response with slots for week view."""

    slots: list[WeeklyPlanSlotResponse] = Field(default_factory=list)
    completion_summary: CompletionSummary

    @classmethod
    def from_orm_with_computed(cls, obj, slots: list) -> "WeeklyPlanInstanceDayResponse":
        """Create response from ORM object with computed fields."""
        completed_count = sum(1 for s in slots if s.completion_status is not None)
        return cls(
            date=obj.date,
            weekday=WEEKDAY_NAMES.get(obj.date.weekday(), "Unknown"),
            template=DayTemplateCompact.model_validate(obj.day_template) if obj.day_template else None,
            is_override=obj.is_override,
            override_reason=obj.override_reason,
            slots=[WeeklyPlanSlotResponse.model_validate(s) for s in slots],
            completion_summary=CompletionSummary(
                completed=completed_count,
                total=len(slots),
            ),
        )


class WeeklyPlanInstanceResponse(BaseSchema):
    """Full weekly plan instance response for GET /weekly-plans/current."""

    id: UUID
    week_start_date: date
    week_plan: WeekPlanCompact | None = None
    days: list[WeeklyPlanInstanceDayResponse] = Field(default_factory=list)


class WeeklyPlanGenerateRequest(BaseSchema):
    """Request to generate a new weekly plan."""

    week_start_date: date | None = Field(
        default=None,
        description="Monday of the target week. Defaults to next Monday if not provided.",
    )


class SwitchTemplateRequest(BaseSchema):
    """Request to switch a day's template."""

    day_template_id: UUID = Field(description="New template to use for the day")


class SetOverrideRequest(BaseSchema):
    """Request to mark a day as 'no plan' override."""

    reason: str | None = Field(
        default=None,
        max_length=255,
        description="Reason for the override (e.g., 'LAN party')",
    )


class OverrideResponse(BaseSchema):
    """Response after setting/clearing an override."""

    date: date
    is_override: bool
    override_reason: str | None = None


class AddAdhocSlotRequest(BaseSchema):
    """Request to add an ad-hoc meal to today."""

    meal_id: UUID = Field(description="ID of the meal to add")


class CompleteSlotRequest(BaseSchema):
    """Request to mark a slot as complete.

    Per ADR-012, equivalent/deviated statuses can include an actual_meal_id
    to record what was actually eaten.
    """

    status: CompletionStatus = Field(description="Completion status")
    actual_meal_id: UUID | None = Field(
        default=None,
        description="ID of the meal actually eaten (for equivalent/deviated statuses)",
    )


class CompleteSlotResponse(BaseSchema):
    """Response after completing a slot."""

    id: UUID
    completion_status: CompletionStatus | None = None
    completed_at: datetime | None = None
    actual_meal: MealCompact | None = None


class ReassignSlotRequest(BaseSchema):
    """Request to reassign a slot's meal."""

    meal_id: UUID = Field(description="ID of the new meal to assign")
    meal_type_id: UUID | None = Field(
        default=None,
        description="Optional: change the slot's meal type as well",
    )
