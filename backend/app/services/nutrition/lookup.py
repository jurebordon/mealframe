"""Unified nutrition lookup service with per-ingredient DB cache (ADR-015).

The lookup picks a preferred upstream based on ``hint``:
- ``whole_food`` (default)  →  USDA first, Open Food Facts fallback
- ``branded``               →  Open Food Facts first, USDA fallback

Two-layer cache (``nutrition_cache`` table):
1. ``search`` rows map a normalized query string to an upstream external id
2. ``item`` rows map an external id to the normalized macros + raw upstream payload

On upstream error or empty results from both sources, returns ``NutritionResult.empty()``
so the caller can decide how to fall back (e.g., ask an LLM for estimates).
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.nutrition_cache import NutritionCache
from app.schemas.nutrition import (
    NormalizedMacros,
    NutritionConfidence,
    NutritionResult,
    NutritionSource,
)

from . import open_food_facts_client as off_client
from . import usda_client
from .errors import NutritionUpstreamError

Hint = Literal["whole_food", "branded"]


def _normalize_query(query: str) -> str:
    return " ".join(query.lower().strip().split())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _search_ttl() -> timedelta:
    return timedelta(days=settings.nutrition_cache_search_ttl_days)


def _item_ttl() -> timedelta:
    return timedelta(days=settings.nutrition_cache_item_ttl_days)


async def _cache_get(
    db: AsyncSession,
    source: NutritionSource,
    cache_type: str,
    cache_key: str,
) -> NutritionCache | None:
    stmt = select(NutritionCache).where(
        and_(
            NutritionCache.source == source.value,
            NutritionCache.cache_type == cache_type,
            NutritionCache.cache_key == cache_key,
            NutritionCache.expires_at > _now(),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _cache_put(
    db: AsyncSession,
    *,
    source: NutritionSource,
    cache_type: str,
    cache_key: str,
    payload_json: dict[str, Any],
    normalized_macros: dict[str, Any] | None,
    ttl: timedelta,
) -> None:
    # Remove any expired/stale row for the same key first so the unique index is free.
    existing_stmt = select(NutritionCache).where(
        and_(
            NutritionCache.source == source.value,
            NutritionCache.cache_type == cache_type,
            NutritionCache.cache_key == cache_key,
        )
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        await db.delete(existing)
        await db.flush()

    row = NutritionCache(
        source=source.value,
        cache_type=cache_type,
        cache_key=cache_key,
        payload_json=payload_json,
        normalized_macros=normalized_macros,
        expires_at=_now() + ttl,
    )
    db.add(row)
    await db.flush()


def _macros_to_json(macros: NormalizedMacros) -> dict[str, Any]:
    return {
        "calories_kcal": macros.calories_kcal,
        "protein_g": str(macros.protein_g),
        "fat_g": str(macros.fat_g),
        "carbs_g": str(macros.carbs_g),
        "per_grams": str(macros.per_grams),
    }


def _macros_from_json(data: dict[str, Any]) -> NormalizedMacros:
    return NormalizedMacros(
        calories_kcal=int(data["calories_kcal"]),
        protein_g=Decimal(str(data["protein_g"])),
        fat_g=Decimal(str(data["fat_g"])),
        carbs_g=Decimal(str(data["carbs_g"])),
        per_grams=Decimal(str(data["per_grams"])),
    )


# ---------------------------------------------------------------------------
# USDA path
# ---------------------------------------------------------------------------


async def _lookup_usda(
    db: AsyncSession, normalized: str
) -> NutritionResult | None:
    """Return a verified USDA result, or None if USDA has no usable data."""
    source = NutritionSource.USDA

    # Search layer
    search_row = await _cache_get(db, source, "search", normalized)
    if search_row is not None:
        external_id = str(search_row.payload_json.get("external_id"))
        display_name = search_row.payload_json.get("display_name")
    else:
        hits = await usda_client.search_foods(normalized, limit=1)
        if not hits:
            return None
        top = hits[0]
        external_id = str(top.get("fdcId"))
        display_name = top.get("description")
        await _cache_put(
            db,
            source=source,
            cache_type="search",
            cache_key=normalized,
            payload_json={
                "external_id": external_id,
                "display_name": display_name,
                "top_hit": top,
            },
            normalized_macros=None,
            ttl=_search_ttl(),
        )

    # Item layer
    item_row = await _cache_get(db, source, "item", external_id)
    if item_row is not None and item_row.normalized_macros:
        macros = _macros_from_json(item_row.normalized_macros)
        return NutritionResult(
            source=source,
            confidence=NutritionConfidence.VERIFIED,
            external_id=external_id,
            display_name=display_name,
            macros=macros,
            raw=item_row.payload_json,
        )

    food = await usda_client.get_food(external_id)
    if food is None:
        return None
    macros = usda_client.normalize_usda_food(food)
    if macros is None:
        return None

    await _cache_put(
        db,
        source=source,
        cache_type="item",
        cache_key=external_id,
        payload_json=food,
        normalized_macros=_macros_to_json(macros),
        ttl=_item_ttl(),
    )
    return NutritionResult(
        source=source,
        confidence=NutritionConfidence.VERIFIED,
        external_id=external_id,
        display_name=display_name or food.get("description"),
        macros=macros,
        raw=food,
    )


# ---------------------------------------------------------------------------
# Open Food Facts path
# ---------------------------------------------------------------------------


async def _lookup_off(
    db: AsyncSession, normalized: str
) -> NutritionResult | None:
    """Return a verified Open Food Facts result, or None if no usable data."""
    source = NutritionSource.OPEN_FOOD_FACTS

    search_row = await _cache_get(db, source, "search", normalized)
    if search_row is not None:
        external_id = str(search_row.payload_json.get("external_id"))
        display_name = search_row.payload_json.get("display_name")
    else:
        products = await off_client.search_products(normalized, limit=1)
        if not products:
            return None
        top = products[0]
        external_id = str(top.get("code") or top.get("_id") or "")
        if not external_id:
            return None
        display_name = top.get("product_name") or top.get("generic_name")
        await _cache_put(
            db,
            source=source,
            cache_type="search",
            cache_key=normalized,
            payload_json={
                "external_id": external_id,
                "display_name": display_name,
                "top_hit": top,
            },
            normalized_macros=None,
            ttl=_search_ttl(),
        )

    item_row = await _cache_get(db, source, "item", external_id)
    if item_row is not None and item_row.normalized_macros:
        macros = _macros_from_json(item_row.normalized_macros)
        return NutritionResult(
            source=source,
            confidence=NutritionConfidence.VERIFIED,
            external_id=external_id,
            display_name=display_name,
            macros=macros,
            raw=item_row.payload_json,
        )

    product = await off_client.get_product(external_id)
    if product is None:
        return None
    macros = off_client.normalize_off_product(product)
    if macros is None:
        return None

    await _cache_put(
        db,
        source=source,
        cache_type="item",
        cache_key=external_id,
        payload_json=product,
        normalized_macros=_macros_to_json(macros),
        ttl=_item_ttl(),
    )
    return NutritionResult(
        source=source,
        confidence=NutritionConfidence.VERIFIED,
        external_id=external_id,
        display_name=display_name or product.get("product_name"),
        macros=macros,
        raw=product,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def lookup_ingredient(
    db: AsyncSession,
    query: str,
    *,
    hint: Hint | None = None,
) -> NutritionResult:
    """
    Look up nutrition for a single ingredient query.

    Preferred source is chosen from ``hint``; the other source is tried as a fallback
    when the preferred source yields no usable data. Upstream errors are caught per
    source — if *both* sources fail or return no data, ``NutritionResult.empty()`` is
    returned so the caller can decide how to recover.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return NutritionResult.empty()

    if hint == "branded":
        order = (_lookup_off, _lookup_usda)
    else:
        order = (_lookup_usda, _lookup_off)

    for lookup in order:
        try:
            result = await lookup(db, normalized)
        except NutritionUpstreamError:
            continue
        if result is not None:
            return result

    return NutritionResult.empty()
