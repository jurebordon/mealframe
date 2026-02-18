"""Pydantic schemas for Stats/Adherence responses."""
from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from .base import BaseSchema


class StatusBreakdown(BaseSchema):
    """Breakdown of completion statuses."""

    followed: int = Field(default=0, description="Meals eaten as planned")
    adjusted: int = Field(default=0, description="Meals with portion adjustments")
    skipped: int = Field(default=0, description="Meals skipped entirely")
    replaced: int = Field(default=0, description="Meals replaced with something else")
    social: int = Field(default=0, description="Meals skipped for social events")
    unmarked: int = Field(default=0, description="Meals not yet marked")


class MealTypeAdherence(BaseSchema):
    """Adherence breakdown for a single meal type."""

    meal_type_id: UUID
    name: str
    total: int = Field(description="Total slots for this meal type")
    followed: int = Field(description="Slots marked as followed")
    adherence_rate: Decimal = Field(
        description="Adherence rate (0.0-1.0)",
        ge=0,
        le=1,
    )


class DailyAdherence(BaseSchema):
    """Adherence data for a single day (used in daily chart)."""

    date: date
    total: int = Field(description="Total slots for this day")
    followed: int = Field(description="Slots followed or adjusted")
    adherence_rate: Decimal = Field(
        description="Adherence rate for this day (0.0-1.0)",
        ge=0,
        le=1,
    )


class OverLimitBreakdown(BaseSchema):
    """Over-limit breakdown for a single day template."""

    template_name: str = Field(description="Day template name")
    days_over: int = Field(description="Days where actual exceeded limit")
    total_days: int = Field(description="Total days this template was used (with limits set)")
    exceeded_metric: str = Field(description="Which metric was exceeded: 'calories', 'protein', or 'both'")


class StatsResponse(BaseSchema):
    """Response for GET /stats.

    Per Tech Spec section 4.3, provides adherence statistics for reflection.
    Adherence calculation: (followed + adjusted) / (total - social - unmarked)
    """

    period_days: int = Field(description="Number of days analyzed")
    total_slots: int = Field(description="Total meal slots in period")
    completed_slots: int = Field(description="Slots with any completion status")
    by_status: StatusBreakdown = Field(description="Breakdown by completion status")
    adherence_rate: Decimal = Field(
        description="Overall adherence rate (0.0-1.0)",
        ge=0,
        le=1,
    )
    current_streak: int = Field(description="Current streak in days")
    best_streak: int = Field(description="Best streak in days")
    override_days: int = Field(description="Number of 'no plan' days in period")
    by_meal_type: list[MealTypeAdherence] = Field(
        default_factory=list,
        description="Adherence breakdown by meal type, sorted by lowest adherence first",
    )
    daily_adherence: list[DailyAdherence] = Field(
        default_factory=list,
        description="Per-day adherence data points for charting, ordered by date ascending",
    )
    avg_daily_calories: Decimal | None = Field(
        default=None,
        description="Average daily calories across days with meal data",
    )
    avg_daily_protein: Decimal | None = Field(
        default=None,
        description="Average daily protein (g) across days with meal data",
    )
    over_limit_days: int = Field(default=0, description="Days where actual macros exceeded template soft limits")
    days_with_limits: int = Field(default=0, description="Days that had a template with soft limits set")
    over_limit_breakdown: list[OverLimitBreakdown] = Field(
        default_factory=list,
        description="Per-template breakdown of over-limit days",
    )


class StatsQueryParams(BaseSchema):
    """Query parameters for GET /stats."""

    days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to analyze",
    )
