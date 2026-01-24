"""Pydantic schemas for DayTemplate and DayTemplateSlot entities."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseSchema
from .meal_type import MealTypeCompact


class DayTemplateSlotBase(BaseSchema):
    """Base fields for a slot within a day template."""

    position: int = Field(ge=1, description="Sequence order (1, 2, 3...)")
    meal_type_id: UUID = Field(description="Meal type for this slot")


class DayTemplateSlotCreate(DayTemplateSlotBase):
    """Schema for creating a slot when creating/updating a template."""

    pass


class DayTemplateSlotResponse(BaseSchema):
    """Slot response with expanded meal type info."""

    id: UUID
    position: int
    meal_type: MealTypeCompact


class DayTemplateBase(BaseSchema):
    """Base fields for DayTemplate - shared between create/update."""

    name: str = Field(min_length=1, max_length=255, description="Display name")
    notes: str | None = Field(default=None, description="Usage context")


class DayTemplateCreate(DayTemplateBase):
    """Schema for creating a new DayTemplate with slots."""

    slots: list[DayTemplateSlotCreate] = Field(
        default_factory=list,
        description="Ordered list of meal type slots",
    )


class DayTemplateUpdate(BaseSchema):
    """Schema for updating a DayTemplate - all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    slots: list[DayTemplateSlotCreate] | None = Field(
        default=None,
        description="Replace all slots with this list (deletes existing slots)",
    )


class DayTemplateResponse(DayTemplateBase):
    """Full DayTemplate response with slots."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    slots: list[DayTemplateSlotResponse] = Field(
        default_factory=list, description="Ordered meal type slots"
    )


class DayTemplateCompact(BaseSchema):
    """Compact DayTemplate for embedding in other responses."""

    id: UUID
    name: str


class DayTemplateListItem(BaseSchema):
    """DayTemplate item for list views."""

    id: UUID
    name: str
    notes: str | None = None
    slot_count: int = Field(description="Number of meal slots in this template")
    slot_preview: str | None = Field(
        default=None,
        description="Preview of slot sequence (e.g., 'Breakfast → Lunch → Dinner')",
    )
