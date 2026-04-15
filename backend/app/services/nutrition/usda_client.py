"""USDA FoodData Central API client.

Docs: https://fdc.nal.usda.gov/api-guide.html
Search:  GET /fdc/v1/foods/search
Detail:  GET /fdc/v1/food/{fdcId}
"""
from decimal import Decimal
from typing import Any

import httpx

from app.config import settings
from app.schemas.nutrition import NormalizedMacros

from ._http import async_client
from .errors import NutritionUpstreamError

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
_TIMEOUT = httpx.Timeout(5.0, connect=3.0)

# USDA nutrient names we care about. Units are grams unless noted.
_NUTRIENT_ENERGY = "Energy"
_NUTRIENT_PROTEIN = "Protein"
_NUTRIENT_FAT = "Total lipid (fat)"
_NUTRIENT_CARBS = "Carbohydrate, by difference"


async def search_foods(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Search USDA for foods matching ``query``. Returns the ``foods`` list (possibly empty)."""
    if not settings.usda_api_key:
        raise NutritionUpstreamError("usda", "USDA_API_KEY not configured")

    params = {
        "api_key": settings.usda_api_key,
        "query": query,
        "pageSize": limit,
        "dataType": "Foundation,SR Legacy,Survey (FNDDS)",
    }
    try:
        async with async_client(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{USDA_BASE_URL}/foods/search", params=params)
    except httpx.HTTPError as exc:
        raise NutritionUpstreamError("usda", f"search failed: {exc}") from exc

    if resp.status_code != 200:
        raise NutritionUpstreamError(
            "usda", f"search returned {resp.status_code}: {resp.text[:200]}"
        )
    data = resp.json()
    return list(data.get("foods", []))


async def get_food(fdc_id: int | str) -> dict[str, Any] | None:
    """Fetch a USDA food by fdcId. Returns None on 404."""
    if not settings.usda_api_key:
        raise NutritionUpstreamError("usda", "USDA_API_KEY not configured")

    params = {"api_key": settings.usda_api_key}
    try:
        async with async_client(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{USDA_BASE_URL}/food/{fdc_id}", params=params)
    except httpx.HTTPError as exc:
        raise NutritionUpstreamError("usda", f"food fetch failed: {exc}") from exc

    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise NutritionUpstreamError(
            "usda", f"food fetch returned {resp.status_code}: {resp.text[:200]}"
        )
    return resp.json()


def _extract_nutrient(food: dict[str, Any], name: str) -> float | None:
    """Pull a nutrient amount out of a USDA food payload (per 100g basis)."""
    for nutrient in food.get("foodNutrients", []):
        # Shape varies between search hits and detail fetches — handle both.
        nutrient_name = (
            nutrient.get("nutrientName")
            or nutrient.get("nutrient", {}).get("name")
            or ""
        )
        if nutrient_name == name:
            value = nutrient.get("value")
            if value is None:
                value = nutrient.get("amount")
            if value is not None:
                return float(value)
    return None


def normalize_usda_food(food: dict[str, Any]) -> NormalizedMacros | None:
    """Normalize a USDA food payload into per-100g macros."""
    energy = _extract_nutrient(food, _NUTRIENT_ENERGY)
    protein = _extract_nutrient(food, _NUTRIENT_PROTEIN)
    fat = _extract_nutrient(food, _NUTRIENT_FAT)
    carbs = _extract_nutrient(food, _NUTRIENT_CARBS)

    if energy is None or protein is None or fat is None or carbs is None:
        return None

    return NormalizedMacros(
        calories_kcal=int(round(energy)),
        protein_g=Decimal(str(protein)),
        fat_g=Decimal(str(fat)),
        carbs_g=Decimal(str(carbs)),
        per_grams=Decimal("100"),
    )
