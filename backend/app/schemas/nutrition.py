"""Pydantic schemas for nutrition lookup (ADR-015)."""
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class NutritionSource(str, Enum):
    """Where a nutrition result came from."""

    USDA = "usda"
    OPEN_FOOD_FACTS = "open_food_facts"
    NONE = "none"


class NutritionConfidence(str, Enum):
    """Confidence in a nutrition result."""

    VERIFIED = "verified"  # Real data from an authoritative API
    NONE = "none"  # No data; caller must decide fallback


class NormalizedMacros(BaseModel):
    """Macros normalized per N grams of the ingredient."""

    calories_kcal: int
    protein_g: Decimal
    fat_g: Decimal
    carbs_g: Decimal
    per_grams: Decimal  # Serving size the macros apply to (typically 100)

    model_config = ConfigDict(from_attributes=True)


class NutritionResult(BaseModel):
    """
    Result of a nutrition lookup.

    When ``source == NONE`` / ``confidence == NONE``, macros is ``None`` and the caller
    is responsible for any fallback (e.g., asking an LLM to estimate).
    """

    source: NutritionSource
    confidence: NutritionConfidence
    external_id: str | None = None
    display_name: str | None = None
    macros: NormalizedMacros | None = None
    raw: dict[str, Any] | None = None

    @classmethod
    def empty(cls) -> "NutritionResult":
        """Return a zero-data result for downstream fallback handling."""
        return cls(source=NutritionSource.NONE, confidence=NutritionConfidence.NONE)
