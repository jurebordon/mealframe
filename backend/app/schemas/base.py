"""Base Pydantic schema utilities for MealFrame API."""
from datetime import datetime
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration for all MealFrame schemas."""

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode (formerly orm_mode)
        populate_by_name=True,  # Allow population by field name or alias
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v) if v else None,
        },
    )


class TimestampMixin(BaseModel):
    """Mixin for models with created_at and updated_at timestamps."""

    created_at: datetime
    updated_at: datetime


# Type variable for generic schema operations
SchemaType = TypeVar("SchemaType", bound=BaseSchema)
