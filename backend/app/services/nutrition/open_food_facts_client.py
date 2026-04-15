"""Open Food Facts API client.

Docs: https://openfoodfacts.github.io/openfoodfacts-server/api/
Search:  GET /cgi/search.pl?search_terms=...&json=1
Detail:  GET /api/v2/product/{barcode}.json
"""
from decimal import Decimal
from typing import Any

import httpx

from app.config import settings
from app.schemas.nutrition import NormalizedMacros

from ._http import async_client
from .errors import NutritionUpstreamError

OFF_BASE_URL = "https://world.openfoodfacts.org"
_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


def _headers() -> dict[str, str]:
    # Open Food Facts requires a descriptive User-Agent.
    return {"User-Agent": settings.open_food_facts_user_agent}


async def search_products(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Search Open Food Facts by free-text query."""
    params = {
        "search_terms": query,
        "search_simple": "1",
        "action": "process",
        "json": "1",
        "page_size": limit,
    }
    try:
        async with async_client(timeout=_TIMEOUT, headers=_headers()) as client:
            resp = await client.get(f"{OFF_BASE_URL}/cgi/search.pl", params=params)
    except httpx.HTTPError as exc:
        raise NutritionUpstreamError("open_food_facts", f"search failed: {exc}") from exc

    if resp.status_code != 200:
        raise NutritionUpstreamError(
            "open_food_facts", f"search returned {resp.status_code}"
        )
    data = resp.json()
    return list(data.get("products", []))


async def get_product(barcode: str) -> dict[str, Any] | None:
    """Fetch a single OFF product by barcode. Returns None if not found."""
    try:
        async with async_client(timeout=_TIMEOUT, headers=_headers()) as client:
            resp = await client.get(f"{OFF_BASE_URL}/api/v2/product/{barcode}.json")
    except httpx.HTTPError as exc:
        raise NutritionUpstreamError(
            "open_food_facts", f"product fetch failed: {exc}"
        ) from exc

    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise NutritionUpstreamError(
            "open_food_facts", f"product fetch returned {resp.status_code}"
        )
    data = resp.json()
    if data.get("status") == 0:
        return None
    return data.get("product")


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_off_product(product: dict[str, Any]) -> NormalizedMacros | None:
    """Normalize an OFF product payload into per-100g macros."""
    nutriments = product.get("nutriments") or {}
    energy = _num(nutriments.get("energy-kcal_100g"))
    if energy is None:
        # Fallback: energy in kJ → convert to kcal.
        kj = _num(nutriments.get("energy_100g"))
        if kj is not None:
            energy = kj / 4.184
    protein = _num(nutriments.get("proteins_100g"))
    fat = _num(nutriments.get("fat_100g"))
    carbs = _num(nutriments.get("carbohydrates_100g"))

    if energy is None or protein is None or fat is None or carbs is None:
        return None

    return NormalizedMacros(
        calories_kcal=int(round(energy)),
        protein_g=Decimal(str(protein)),
        fat_g=Decimal(str(fat)),
        carbs_g=Decimal(str(carbs)),
        per_grams=Decimal("100"),
    )
