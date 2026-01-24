"""Pydantic schemas for Today/Yesterday view responses."""
from datetime import date

from pydantic import Field

from .base import BaseSchema
from .day_template import DayTemplateCompact
from .weekly_plan import WeeklyPlanSlotWithNext


class TodayStats(BaseSchema):
    """Statistics for the Today view header."""

    completed: int = Field(description="Number of completed meals today")
    total: int = Field(description="Total number of meals today")
    streak_days: int = Field(description="Current streak in days")


class TodayResponse(BaseSchema):
    """Response for GET /today and GET /yesterday.

    Per Tech Spec section 4.3, this is the primary daily use endpoint.
    The `is_next` field on each slot indicates the next meal to complete.
    """

    date: date
    weekday: str = Field(description="Human-readable weekday (e.g., 'Tuesday')")
    template: DayTemplateCompact | None = Field(
        default=None,
        description="Day template used (e.g., 'Morning Workout Workday')",
    )
    is_override: bool = Field(
        default=False,
        description="True if this is a 'no plan' override day",
    )
    override_reason: str | None = Field(
        default=None,
        description="Reason for override if applicable",
    )
    slots: list[WeeklyPlanSlotWithNext] = Field(
        default_factory=list,
        description="Meal slots with completion status and is_next indicator",
    )
    stats: TodayStats = Field(description="Daily progress and streak statistics")


class YesterdayReviewResponse(BaseSchema):
    """Response for Yesterday Review modal.

    Shows only unmarked meals from yesterday for quick catch-up.
    """

    date: date
    weekday: str
    unmarked_count: int = Field(description="Number of unmarked meals")
    unmarked_slots: list[WeeklyPlanSlotWithNext] = Field(
        default_factory=list,
        description="Slots without completion status",
    )
