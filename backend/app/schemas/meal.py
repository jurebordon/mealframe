"""Pydantic schemas for Meal entity."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from .base import BaseSchema
from .meal_type import MealTypeCompact


class MealBase(BaseSchema):
    """Base fields for Meal - shared between create/update."""

    name: str = Field(min_length=1, max_length=255, description="Display name")
    portion_description: str = Field(
        min_length=1,
        description="Exact portion (e.g., '2 eggs + 1 slice toast'). REQUIRED per invariant.",
    )
    calories_kcal: int | None = Field(default=None, ge=0, description="Calories for defined portion")
    protein_g: Decimal | None = Field(default=None, ge=0, description="Protein grams")
    carbs_g: Decimal | None = Field(default=None, ge=0, description="Carbohydrate grams")
    sugar_g: Decimal | None = Field(default=None, ge=0, description="Sugar grams (subset of carbs)")
    fat_g: Decimal | None = Field(default=None, ge=0, description="Fat grams")
    saturated_fat_g: Decimal | None = Field(default=None, ge=0, description="Saturated fat grams (subset of fat)")
    fiber_g: Decimal | None = Field(default=None, ge=0, description="Fiber grams")
    notes: str | None = Field(default=None, description="Preparation notes")


class MealCreate(MealBase):
    """Schema for creating a new Meal."""

    meal_type_ids: list[UUID] = Field(
        default_factory=list,
        description="List of meal type IDs to assign this meal to",
    )


class MealUpdate(BaseSchema):
    """Schema for updating a Meal - all fields optional except portion_description if provided."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    portion_description: str | None = Field(default=None, min_length=1)
    calories_kcal: int | None = None
    protein_g: Decimal | None = None
    carbs_g: Decimal | None = None
    sugar_g: Decimal | None = None
    fat_g: Decimal | None = None
    saturated_fat_g: Decimal | None = None
    fiber_g: Decimal | None = None
    notes: str | None = None
    meal_type_ids: list[UUID] | None = Field(
        default=None,
        description="Replace meal type assignments with this list",
    )


class MealResponse(MealBase):
    """Full Meal response with all fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    meal_types: list[MealTypeCompact] = Field(
        default_factory=list, description="Meal types this meal is assigned to"
    )


class MealCompact(BaseSchema):
    """Compact Meal for embedding in slot responses.

    Per Tech Spec GET /today response, includes macros inline.
    """

    id: UUID
    name: str
    portion_description: str
    calories_kcal: int | None = None
    protein_g: Decimal | None = None
    carbs_g: Decimal | None = None
    sugar_g: Decimal | None = None
    fat_g: Decimal | None = None
    saturated_fat_g: Decimal | None = None
    fiber_g: Decimal | None = None


class MealListItem(BaseSchema):
    """Meal item for list views (library screen)."""

    id: UUID
    name: str
    portion_description: str
    calories_kcal: int | None = None
    protein_g: Decimal | None = None
    meal_types: list[MealTypeCompact] = Field(default_factory=list)


class MealImportRow(BaseSchema):
    """Schema for a single row in CSV import.

    Maps to the format expected by POST /meals/import.
    """

    name: str = Field(min_length=1, max_length=255)
    portion_description: str = Field(min_length=1)
    calories_kcal: int | None = None
    protein_g: Decimal | None = None
    carbs_g: Decimal | None = None
    sugar_g: Decimal | None = None
    fat_g: Decimal | None = None
    saturated_fat_g: Decimal | None = None
    fiber_g: Decimal | None = None
    notes: str | None = None
    meal_types: str | None = Field(
        default=None,
        description="Comma-separated meal type names",
    )

    @field_validator("meal_types")
    @classmethod
    def parse_meal_types(cls, v: str | None) -> str | None:
        """Normalize meal types string."""
        if v is None:
            return None
        return v.strip() if v.strip() else None


class MealImportWarning(BaseSchema):
    """A warning from the CSV import process (non-fatal)."""

    row: int = Field(description="Row number (1-based, excluding header)")
    message: str = Field(description="Warning message")


class MealImportError(BaseSchema):
    """An error from the CSV import process (row skipped)."""

    row: int = Field(description="Row number (1-based, excluding header)")
    message: str = Field(description="Error message")


class MealImportSummary(BaseSchema):
    """Summary counts for CSV import."""

    total_rows: int = Field(description="Total rows processed")
    created: int = Field(description="Number of meals created")
    skipped: int = Field(description="Number of rows skipped due to errors")
    warnings: int = Field(description="Number of warnings generated")


class MealImportResult(BaseSchema):
    """Result of CSV meal import operation per frozen spec MEAL_IMPORT_GUIDE.md."""

    success: bool = Field(description="Whether the import completed (even if some rows had errors)")
    summary: MealImportSummary
    warnings: list[MealImportWarning] = Field(default_factory=list)
    errors: list[MealImportError] = Field(default_factory=list)
