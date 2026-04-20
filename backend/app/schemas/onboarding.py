"""Pydantic schemas for onboarding state API."""
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from .base import BaseSchema


# ---------------------------------------------------------------------------
# Generated setup schemas — shape of OnboardingState.generated_setup JSONB.
# Names are used as cross-references (resolved to real IDs in Session 5 apply).
# ---------------------------------------------------------------------------


class GeneratedMealType(BaseSchema):
    """A meal type proposed by the AI (e.g. Breakfast, Lunch)."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)


class GeneratedDayTemplateSlot(BaseSchema):
    """A slot within a generated day template, referencing a meal type by name."""

    position: int = Field(ge=1)
    meal_type_name: str = Field(min_length=1)


class GeneratedDayTemplate(BaseSchema):
    """A day template proposed by the AI (e.g. Workday, Weekend)."""

    name: str = Field(min_length=1, max_length=255)
    notes: str | None = None
    max_calories_kcal: int | None = Field(default=None, ge=1)
    max_protein_g: Decimal | None = Field(default=None, ge=0)
    slots: list[GeneratedDayTemplateSlot] = Field(min_length=1)


class GeneratedWeekPlanDay(BaseSchema):
    """A single day in the generated week plan, referencing a day template by name."""

    weekday: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    day_template_name: str = Field(min_length=1)


class GeneratedWeekPlan(BaseSchema):
    """The week plan proposed by the AI."""

    name: str = Field(min_length=1, max_length=255)
    is_default: bool = True
    days: list[GeneratedWeekPlanDay] = Field(min_length=7, max_length=7)


class GeneratedSetup(BaseSchema):
    """Complete AI-generated setup: meal types, day templates, and week plan.

    Cross-field validators ensure internal consistency:
    - Meal type names are unique.
    - Day template names are unique.
    - Every slot.meal_type_name references an existing meal type.
    - Every day.day_template_name references an existing day template.
    - Week plan covers all 7 weekdays exactly once.
    """

    meal_types: list[GeneratedMealType] = Field(min_length=1, max_length=10)
    day_templates: list[GeneratedDayTemplate] = Field(min_length=1, max_length=7)
    week_plan: GeneratedWeekPlan

    @model_validator(mode="after")
    def validate_references(self) -> "GeneratedSetup":
        # Unique meal type names
        mt_names = [mt.name for mt in self.meal_types]
        if len(mt_names) != len(set(mt_names)):
            raise ValueError("Duplicate meal type names")

        # Unique day template names
        dt_names = [dt.name for dt in self.day_templates]
        if len(dt_names) != len(set(dt_names)):
            raise ValueError("Duplicate day template names")

        mt_name_set = set(mt_names)
        dt_name_set = set(dt_names)

        # Slot references
        for dt in self.day_templates:
            for slot in dt.slots:
                if slot.meal_type_name not in mt_name_set:
                    raise ValueError(
                        f"Day template '{dt.name}' slot references unknown "
                        f"meal type '{slot.meal_type_name}'"
                    )

        # Week plan day references
        for day in self.week_plan.days:
            if day.day_template_name not in dt_name_set:
                raise ValueError(
                    f"Week plan day {day.weekday} references unknown "
                    f"day template '{day.day_template_name}'"
                )

        # Exactly 7 unique weekdays
        weekdays = [d.weekday for d in self.week_plan.days]
        if sorted(weekdays) != list(range(7)):
            raise ValueError("Week plan must cover weekdays 0-6 exactly once")

        return self


class OnboardingStateResponse(BaseSchema):
    """Full onboarding state returned by GET/POST/PATCH endpoints."""

    id: UUID
    status: str
    intake_substep: int | None = None
    intake_answers: dict[str, Any] = Field(default_factory=dict)
    generated_setup: dict[str, Any] = Field(default_factory=dict)
    chat_messages: list[dict[str, Any]] = Field(default_factory=list)
    imported_meals: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class OnboardingStateUpdate(BaseSchema):
    """Partial update for PATCH endpoint. All fields optional."""

    status: str | None = None
    intake_substep: int | None = Field(default=None, ge=1, le=6)
    intake_answers: dict[str, Any] | None = None
    generated_setup: dict[str, Any] | None = None
    chat_messages: list[dict[str, Any]] | None = None
    imported_meals: list[dict[str, Any]] | None = None
    error_message: str | None = None


class OnboardingStatusResponse(BaseSchema):
    """Lightweight check for frontend routing."""

    has_completed: bool
    has_active: bool
