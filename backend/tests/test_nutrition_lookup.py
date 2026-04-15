"""Tests for the nutrition lookup service (ADR-015 Session 2)."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select

from app.models.nutrition_cache import NutritionCache
from app.schemas.nutrition import NutritionConfidence, NutritionSource
from app.services.nutrition import _http
from app.services.nutrition.lookup import lookup_ingredient
from app.services.nutrition.open_food_facts_client import normalize_off_product
from app.services.nutrition.usda_client import normalize_usda_food

# ---------------------------------------------------------------------------
# Fixture payloads
# ---------------------------------------------------------------------------

USDA_SEARCH_CHICKEN = {
    "foods": [
        {
            "fdcId": 171477,
            "description": "Chicken, broilers or fryers, breast, meat only, raw",
            "dataType": "SR Legacy",
            "foodNutrients": [
                {"nutrientName": "Energy", "value": 120},
                {"nutrientName": "Protein", "value": 22.5},
                {"nutrientName": "Total lipid (fat)", "value": 2.6},
                {"nutrientName": "Carbohydrate, by difference", "value": 0.0},
            ],
        }
    ]
}

USDA_DETAIL_CHICKEN = {
    "fdcId": 171477,
    "description": "Chicken, broilers or fryers, breast, meat only, raw",
    "foodNutrients": [
        {"nutrient": {"name": "Energy"}, "amount": 120},
        {"nutrient": {"name": "Protein"}, "amount": 22.5},
        {"nutrient": {"name": "Total lipid (fat)"}, "amount": 2.6},
        {"nutrient": {"name": "Carbohydrate, by difference"}, "amount": 0.0},
    ],
}

OFF_SEARCH_OAT_BAR = {
    "products": [
        {
            "code": "3017620422003",
            "product_name": "Oat Bar",
            "nutriments": {},
        }
    ]
}

OFF_PRODUCT_OAT_BAR = {
    "status": 1,
    "product": {
        "code": "3017620422003",
        "product_name": "Oat Bar",
        "nutriments": {
            "energy-kcal_100g": 420,
            "proteins_100g": 6.5,
            "fat_100g": 18.0,
            "carbohydrates_100g": 58.0,
        },
    },
}


def make_mock_transport(routes):
    """Build an httpx.MockTransport dispatching by URL substring."""
    def handler(request: httpx.Request) -> httpx.Response:
        for needle, responder in routes.items():
            if needle in str(request.url):
                return responder(request)
        return httpx.Response(404, json={"error": f"no route for {request.url}"})

    return httpx.MockTransport(handler)


@pytest.fixture
def usda_configured(monkeypatch):
    monkeypatch.setattr("app.services.nutrition.usda_client.settings.usda_api_key", "test-key")
    yield


@pytest.fixture
def reset_transport():
    yield
    _http.set_transport(None)


# ---------------------------------------------------------------------------
# Unit tests for normalizers
# ---------------------------------------------------------------------------


def test_normalize_usda_food_extracts_per_100g_macros():
    macros = normalize_usda_food(USDA_DETAIL_CHICKEN)
    assert macros is not None
    assert macros.calories_kcal == 120
    assert macros.protein_g == Decimal("22.5")
    assert macros.fat_g == Decimal("2.6")
    assert macros.carbs_g == Decimal("0.0")
    assert macros.per_grams == Decimal("100")


def test_normalize_usda_food_returns_none_when_missing_nutrient():
    partial = {"foodNutrients": [{"nutrientName": "Energy", "value": 100}]}
    assert normalize_usda_food(partial) is None


def test_normalize_off_product_extracts_macros():
    macros = normalize_off_product(OFF_PRODUCT_OAT_BAR["product"])
    assert macros is not None
    assert macros.calories_kcal == 420
    assert macros.protein_g == Decimal("6.5")


def test_normalize_off_product_falls_back_to_energy_kj():
    product = {
        "nutriments": {
            "energy_100g": 1760,  # kJ; no energy-kcal_100g
            "proteins_100g": 6.5,
            "fat_100g": 18.0,
            "carbohydrates_100g": 58.0,
        }
    }
    macros = normalize_off_product(product)
    assert macros is not None
    assert macros.calories_kcal == pytest.approx(421, abs=1)


# ---------------------------------------------------------------------------
# Integration tests for lookup_ingredient
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_usda_hit_caches_both_layers(db, usda_configured, reset_transport):
    call_counts = {"search": 0, "detail": 0}

    def usda_handler(request):
        url = str(request.url)
        if "/foods/search" in url:
            call_counts["search"] += 1
            return httpx.Response(200, json=USDA_SEARCH_CHICKEN)
        if "/food/171477" in url:
            call_counts["detail"] += 1
            return httpx.Response(200, json=USDA_DETAIL_CHICKEN)
        return httpx.Response(404)

    _http.set_transport(httpx.MockTransport(usda_handler))

    result = await lookup_ingredient(db, "Chicken Breast")

    assert result.source == NutritionSource.USDA
    assert result.confidence == NutritionConfidence.VERIFIED
    assert result.external_id == "171477"
    assert result.macros is not None
    assert result.macros.protein_g == Decimal("22.5")
    assert call_counts == {"search": 1, "detail": 1}

    rows = (
        await db.execute(
            select(NutritionCache).where(NutritionCache.source == "usda")
        )
    ).scalars().all()
    assert {r.cache_type for r in rows} == {"search", "item"}


@pytest.mark.asyncio
async def test_lookup_cache_hit_skips_upstream(db, usda_configured, reset_transport):
    def refuse(request):  # Any upstream call is a bug here.
        raise AssertionError(f"unexpected upstream call: {request.url}")

    # Pre-seed both cache rows.
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            NutritionCache(
                source="usda",
                cache_type="search",
                cache_key="chicken breast",
                payload_json={
                    "external_id": "171477",
                    "display_name": "Chicken, breast",
                    "top_hit": {},
                },
                normalized_macros=None,
                expires_at=now + timedelta(days=30),
            ),
            NutritionCache(
                source="usda",
                cache_type="item",
                cache_key="171477",
                payload_json={"fdcId": 171477},
                normalized_macros={
                    "calories_kcal": 120,
                    "protein_g": "22.5",
                    "fat_g": "2.6",
                    "carbs_g": "0.0",
                    "per_grams": "100",
                },
                expires_at=now + timedelta(days=90),
            ),
        ]
    )
    await db.flush()

    _http.set_transport(httpx.MockTransport(refuse))
    result = await lookup_ingredient(db, "chicken breast")

    assert result.source == NutritionSource.USDA
    assert result.confidence == NutritionConfidence.VERIFIED
    assert result.external_id == "171477"
    assert result.macros.calories_kcal == 120


@pytest.mark.asyncio
async def test_lookup_query_is_normalized(db, usda_configured, reset_transport):
    def refuse(request):
        raise AssertionError(f"unexpected upstream call: {request.url}")

    now = datetime.now(timezone.utc)
    db.add_all(
        [
            NutritionCache(
                source="usda",
                cache_type="search",
                cache_key="chicken breast",
                payload_json={"external_id": "171477", "display_name": "X", "top_hit": {}},
                normalized_macros=None,
                expires_at=now + timedelta(days=30),
            ),
            NutritionCache(
                source="usda",
                cache_type="item",
                cache_key="171477",
                payload_json={},
                normalized_macros={
                    "calories_kcal": 120,
                    "protein_g": "22.5",
                    "fat_g": "2.6",
                    "carbs_g": "0.0",
                    "per_grams": "100",
                },
                expires_at=now + timedelta(days=90),
            ),
        ]
    )
    await db.flush()

    _http.set_transport(httpx.MockTransport(refuse))
    # Uppercase, extra whitespace — should still hit the cache.
    result = await lookup_ingredient(db, "   CHICKEN    breast  ")
    assert result.confidence == NutritionConfidence.VERIFIED


@pytest.mark.asyncio
async def test_usda_empty_falls_back_to_off(db, usda_configured, reset_transport):
    def handler(request):
        url = str(request.url)
        if "/foods/search" in url:
            return httpx.Response(200, json={"foods": []})
        if "/cgi/search.pl" in url:
            return httpx.Response(200, json=OFF_SEARCH_OAT_BAR)
        if "/api/v2/product/3017620422003" in url:
            return httpx.Response(200, json=OFF_PRODUCT_OAT_BAR)
        return httpx.Response(404)

    _http.set_transport(httpx.MockTransport(handler))

    result = await lookup_ingredient(db, "oat bar")

    assert result.source == NutritionSource.OPEN_FOOD_FACTS
    assert result.confidence == NutritionConfidence.VERIFIED
    assert result.external_id == "3017620422003"
    assert result.macros.calories_kcal == 420


@pytest.mark.asyncio
async def test_branded_hint_prefers_off(db, usda_configured, reset_transport):
    seen = []

    def handler(request):
        url = str(request.url)
        seen.append(url)
        if "/cgi/search.pl" in url:
            return httpx.Response(200, json=OFF_SEARCH_OAT_BAR)
        if "/api/v2/product/" in url:
            return httpx.Response(200, json=OFF_PRODUCT_OAT_BAR)
        return httpx.Response(500)

    _http.set_transport(httpx.MockTransport(handler))

    result = await lookup_ingredient(db, "oat bar", hint="branded")
    assert result.source == NutritionSource.OPEN_FOOD_FACTS
    # First call must be OFF, not USDA.
    assert "/cgi/search.pl" in seen[0]


@pytest.mark.asyncio
async def test_upstream_errors_return_none_result(db, usda_configured, reset_transport):
    def handler(request):
        return httpx.Response(500, json={"error": "boom"})

    _http.set_transport(httpx.MockTransport(handler))

    result = await lookup_ingredient(db, "mystery food")
    assert result.source == NutritionSource.NONE
    assert result.confidence == NutritionConfidence.NONE
    assert result.macros is None


@pytest.mark.asyncio
async def test_expired_cache_row_is_ignored(db, usda_configured, reset_transport):
    call_counts = {"search": 0, "detail": 0}

    def handler(request):
        url = str(request.url)
        if "/foods/search" in url:
            call_counts["search"] += 1
            return httpx.Response(200, json=USDA_SEARCH_CHICKEN)
        if "/food/171477" in url:
            call_counts["detail"] += 1
            return httpx.Response(200, json=USDA_DETAIL_CHICKEN)
        return httpx.Response(404)

    # Expired search row — should be ignored.
    past = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(
        NutritionCache(
            source="usda",
            cache_type="search",
            cache_key="chicken breast",
            payload_json={"external_id": "old", "display_name": "stale", "top_hit": {}},
            normalized_macros=None,
            expires_at=past,
        )
    )
    await db.flush()

    _http.set_transport(httpx.MockTransport(handler))

    result = await lookup_ingredient(db, "chicken breast")
    assert result.external_id == "171477"
    assert call_counts == {"search": 1, "detail": 1}


@pytest.mark.asyncio
async def test_usda_missing_api_key_falls_back_to_off(db, monkeypatch, reset_transport):
    monkeypatch.setattr(
        "app.services.nutrition.usda_client.settings.usda_api_key", ""
    )

    def handler(request):
        url = str(request.url)
        if "/cgi/search.pl" in url:
            return httpx.Response(200, json=OFF_SEARCH_OAT_BAR)
        if "/api/v2/product/" in url:
            return httpx.Response(200, json=OFF_PRODUCT_OAT_BAR)
        return httpx.Response(500)

    _http.set_transport(httpx.MockTransport(handler))

    result = await lookup_ingredient(db, "oat bar")
    assert result.source == NutritionSource.OPEN_FOOD_FACTS
