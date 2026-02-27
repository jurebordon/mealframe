"""
Integration tests for the Meal CRUD API endpoints.

Tests cover:
- GET /api/v1/meals - List meals (paginated, search, filter)
- GET /api/v1/meals/{id} - Get single meal
- POST /api/v1/meals - Create meal
- PUT /api/v1/meals/{id} - Update meal
- DELETE /api/v1/meals/{id} - Delete meal

These tests verify:
- CRUD operations work correctly
- Pagination returns correct metadata
- Search filters by meal name (case-insensitive)
- Meal type filter works
- Meal type associations are created/updated/deleted
- 404 for non-existent meals
- Validation errors for invalid data
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Meal, MealType, User
from app.models.meal_to_meal_type import meal_to_meal_type
from app.database import get_db


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Create an async HTTP client with database override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_meal_types(db: AsyncSession, test_user: User) -> list[MealType]:
    """Create sample meal types for testing."""
    suffix = uuid4().hex[:8]
    types = []
    for name in ["Breakfast", "Lunch", "Dinner"]:
        mt = MealType(id=uuid4(), user_id=test_user.id, name=f"{name} {suffix}", description=f"Test {name}")
        db.add(mt)
        types.append(mt)
    await db.flush()
    return types


@pytest_asyncio.fixture
async def sample_meal(db: AsyncSession, test_user: User, sample_meal_types: list[MealType]) -> Meal:
    """Create a sample meal with meal type associations."""
    meal = Meal(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Test Scrambled Eggs {uuid4().hex[:8]}",
        portion_description="2 eggs + 1 slice toast",
        calories_kcal=320,
        protein_g=18,
        carbs_g=15,
        fat_g=22,
        notes="Use whole wheat toast",
    )
    db.add(meal)
    await db.flush()

    # Associate with first meal type (Breakfast)
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id,
            meal_type_id=sample_meal_types[0].id,
        )
    )
    await db.flush()
    return meal


# =============================================================================
# GET /api/v1/meals - List meals
# =============================================================================


@pytest.mark.asyncio
async def test_list_meals_returns_paginated_response(client: AsyncClient):
    """GET /meals returns paginated response with correct structure."""
    response = await client.get("/api/v1/meals")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert "total_pages" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_meals_returns_meals(
    client: AsyncClient, sample_meal: Meal, sample_meal_types: list[MealType]
):
    """GET /meals with search returns meals with correct fields and meal type info."""
    # Use search to isolate our test meal from seeded data
    response = await client.get(
        f"/api/v1/meals?search={sample_meal.name}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Find our sample meal in the list
    meal_item = next((m for m in data["items"] if m["id"] == str(sample_meal.id)), None)
    assert meal_item is not None
    assert meal_item["name"] == sample_meal.name
    assert meal_item["portion_description"] == "2 eggs + 1 slice toast"
    assert meal_item["calories_kcal"] == 320
    assert len(meal_item["meal_types"]) == 1
    assert meal_item["meal_types"][0]["name"] == sample_meal_types[0].name


@pytest.mark.asyncio
async def test_list_meals_pagination(
    client: AsyncClient, db: AsyncSession, test_user: User, sample_meal_types: list[MealType]
):
    """GET /meals respects page and page_size parameters."""
    suffix = uuid4().hex[:8]
    # Create 5 meals
    for i in range(5):
        meal = Meal(
            id=uuid4(),
            user_id=test_user.id,
            name=f"Pagination Meal {i} {suffix}",
            portion_description=f"Portion {i}",
        )
        db.add(meal)
    await db.flush()

    # Request page 1 with size 2
    response = await client.get(f"/api/v1/meals?page=1&page_size=2&search={suffix}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3

    # Request page 3 (last page with 1 item)
    response = await client.get(f"/api/v1/meals?page=3&page_size=2&search={suffix}")
    data = response.json()
    assert len(data["items"]) == 1
    assert data["page"] == 3


@pytest.mark.asyncio
async def test_list_meals_search(
    client: AsyncClient, db: AsyncSession, test_user: User
):
    """GET /meals?search= filters by meal name (case-insensitive)."""
    suffix = uuid4().hex[:8]
    # Create meals with distinct names using a unique prefix to avoid seeded data matches
    prefix = f"XTest{suffix}"
    for name in [f"{prefix}ChickenRice", f"{prefix}SalmonBowl", f"{prefix}ChickenSalad"]:
        meal = Meal(id=uuid4(), user_id=test_user.id, name=name, portion_description="Test portion")
        db.add(meal)
    await db.flush()

    # Search for the prefix + Chicken
    response = await client.get(f"/api/v1/meals?search={prefix}Chicken")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all("Chicken" in item["name"] for item in data["items"])


@pytest.mark.asyncio
async def test_list_meals_filter_by_meal_type(
    client: AsyncClient, db: AsyncSession, test_user: User, sample_meal_types: list[MealType]
):
    """GET /meals?meal_type_id= filters by meal type."""
    suffix = uuid4().hex[:8]
    # Create two meals: one breakfast, one lunch
    breakfast_meal = Meal(
        id=uuid4(), user_id=test_user.id, name=f"Oatmeal {suffix}", portion_description="100g oats"
    )
    lunch_meal = Meal(
        id=uuid4(), user_id=test_user.id, name=f"Sandwich {suffix}", portion_description="2 slices bread"
    )
    db.add(breakfast_meal)
    db.add(lunch_meal)
    await db.flush()

    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=breakfast_meal.id, meal_type_id=sample_meal_types[0].id
        )
    )
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=lunch_meal.id, meal_type_id=sample_meal_types[1].id
        )
    )
    await db.flush()

    # Filter by Breakfast type
    response = await client.get(
        f"/api/v1/meals?meal_type_id={sample_meal_types[0].id}&search={suffix}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == f"Oatmeal {suffix}"


# =============================================================================
# GET /api/v1/meals/{id} - Get single meal
# =============================================================================


@pytest.mark.asyncio
async def test_get_meal_by_id(
    client: AsyncClient, sample_meal: Meal, sample_meal_types: list[MealType]
):
    """GET /meals/{id} returns full meal detail with all fields."""
    response = await client.get(f"/api/v1/meals/{sample_meal.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_meal.id)
    assert data["name"] == sample_meal.name
    assert data["portion_description"] == "2 eggs + 1 slice toast"
    assert data["calories_kcal"] == 320
    assert float(data["protein_g"]) == 18.0
    assert float(data["carbs_g"]) == 15.0
    assert float(data["fat_g"]) == 22.0
    assert data["notes"] == "Use whole wheat toast"
    assert "created_at" in data
    assert "updated_at" in data
    assert len(data["meal_types"]) == 1


@pytest.mark.asyncio
async def test_get_meal_not_found(client: AsyncClient):
    """GET /meals/{id} returns 404 for non-existent meal."""
    fake_id = uuid4()
    response = await client.get(f"/api/v1/meals/{fake_id}")
    assert response.status_code == 404


# =============================================================================
# POST /api/v1/meals - Create meal
# =============================================================================


@pytest.mark.asyncio
async def test_create_meal_minimal(client: AsyncClient):
    """POST /meals creates meal with only required fields."""
    payload = {
        "name": f"Simple Meal {uuid4().hex[:8]}",
        "portion_description": "1 cup rice + 100g chicken",
    }
    response = await client.post("/api/v1/meals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["portion_description"] == payload["portion_description"]
    assert data["calories_kcal"] is None
    assert data["meal_types"] == []
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_meal_full(client: AsyncClient, sample_meal_types: list[MealType]):
    """POST /meals creates meal with all fields and meal type associations."""
    payload = {
        "name": f"Full Meal {uuid4().hex[:8]}",
        "portion_description": "200g salmon + 150g rice + veggies",
        "calories_kcal": 520,
        "protein_g": 38,
        "carbs_g": 48,
        "fat_g": 14,
        "notes": "Bake salmon at 200C for 20 min",
        "meal_type_ids": [str(sample_meal_types[1].id), str(sample_meal_types[2].id)],
    }
    response = await client.post("/api/v1/meals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["calories_kcal"] == 520
    assert data["notes"] == "Bake salmon at 200C for 20 min"
    assert len(data["meal_types"]) == 2
    type_names = {mt["name"] for mt in data["meal_types"]}
    assert sample_meal_types[1].name in type_names
    assert sample_meal_types[2].name in type_names


@pytest.mark.asyncio
async def test_create_meal_missing_name(client: AsyncClient):
    """POST /meals returns 422 when name is missing."""
    payload = {"portion_description": "Some portion"}
    response = await client.post("/api/v1/meals", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_meal_missing_portion(client: AsyncClient):
    """POST /meals returns 422 when portion_description is missing."""
    payload = {"name": "No Portion Meal"}
    response = await client.post("/api/v1/meals", json=payload)
    assert response.status_code == 422


# =============================================================================
# PUT /api/v1/meals/{id} - Update meal
# =============================================================================


@pytest.mark.asyncio
async def test_update_meal_name(client: AsyncClient, sample_meal: Meal):
    """PUT /meals/{id} updates only the provided fields."""
    new_name = f"Updated Eggs {uuid4().hex[:8]}"
    response = await client.put(
        f"/api/v1/meals/{sample_meal.id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    # Other fields unchanged
    assert data["portion_description"] == "2 eggs + 1 slice toast"
    assert data["calories_kcal"] == 320


@pytest.mark.asyncio
async def test_update_meal_types(
    client: AsyncClient, sample_meal: Meal, sample_meal_types: list[MealType]
):
    """PUT /meals/{id} replaces meal type associations when meal_type_ids provided."""
    # Initially has Breakfast, switch to Lunch + Dinner
    response = await client.put(
        f"/api/v1/meals/{sample_meal.id}",
        json={
            "meal_type_ids": [
                str(sample_meal_types[1].id),
                str(sample_meal_types[2].id),
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["meal_types"]) == 2
    type_names = {mt["name"] for mt in data["meal_types"]}
    assert sample_meal_types[1].name in type_names
    assert sample_meal_types[2].name in type_names
    # Original Breakfast type should be gone
    assert sample_meal_types[0].name not in type_names


@pytest.mark.asyncio
async def test_update_meal_not_found(client: AsyncClient):
    """PUT /meals/{id} returns 404 for non-existent meal."""
    fake_id = uuid4()
    response = await client.put(
        f"/api/v1/meals/{fake_id}",
        json={"name": "Doesn't Exist"},
    )
    assert response.status_code == 404


# =============================================================================
# DELETE /api/v1/meals/{id} - Delete meal
# =============================================================================


@pytest.mark.asyncio
async def test_delete_meal(client: AsyncClient, sample_meal: Meal):
    """DELETE /meals/{id} removes the meal and returns 204."""
    response = await client.delete(f"/api/v1/meals/{sample_meal.id}")
    assert response.status_code == 204

    # Confirm it's gone
    response = await client.get(f"/api/v1/meals/{sample_meal.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_meal_not_found(client: AsyncClient):
    """DELETE /meals/{id} returns 404 for non-existent meal."""
    fake_id = uuid4()
    response = await client.delete(f"/api/v1/meals/{fake_id}")
    assert response.status_code == 404
