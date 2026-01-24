"""Pydantic schemas for MealType entity."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import BaseSchema


class MealTypeBase(BaseSchema):
    """Base fields for MealType - shared between create/update."""

    name: str = Field(min_length=1, max_length=255, description="Display name")
    description: str | None = Field(default=None, description="Purpose and intent")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")


class MealTypeCreate(MealTypeBase):
    """Schema for creating a new MealType."""

    pass


class MealTypeUpdate(BaseSchema):
    """Schema for updating a MealType - all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = None


class MealTypeResponse(MealTypeBase):
    """Full MealType response with all fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class MealTypeCompact(BaseSchema):
    """Compact MealType for embedding in other responses (e.g., slots)."""

    id: UUID
    name: str


class MealTypeWithCount(MealTypeResponse):
    """MealType response with count of assigned meals."""

    meal_count: int = Field(description="Number of meals assigned to this type")
