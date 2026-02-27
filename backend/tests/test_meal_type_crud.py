"""
Integration tests for the Meal Type CRUD API endpoints.

Tests cover:
- GET /api/v1/meal-types - List meal types with counts
- GET /api/v1/meal-types/{id} - Get single meal type
- POST /api/v1/meal-types - Create meal type
- PUT /api/v1/meal-types/{id} - Update meal type
- DELETE /api/v1/meal-types/{id} - Delete meal type
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import MealType, Meal, User
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
async def sample_meal_type(db: AsyncSession, test_user: User) -> MealType:
    """Create a sample meal type."""
    mt = MealType(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Test Breakfast {uuid4().hex[:8]}",
        description="Morning meal",
        tags=["morning", "energy"],
    )
    db.add(mt)
    await db.flush()
    return mt


# =============================================================================
# GET /api/v1/meal-types - List meal types
# =============================================================================


@pytest.mark.asyncio
async def test_list_meal_types(client: AsyncClient, sample_meal_type: MealType):
    """GET /meal-types returns list with meal counts."""
    response = await client.get("/api/v1/meal-types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Find our sample meal type
    mt = next((t for t in data if t["id"] == str(sample_meal_type.id)), None)
    assert mt is not None
    assert mt["name"] == sample_meal_type.name
    assert mt["description"] == "Morning meal"
    assert mt["meal_count"] == 0


@pytest.mark.asyncio
async def test_list_meal_types_with_meal_count(
    client: AsyncClient, db: AsyncSession, test_user: User, sample_meal_type: MealType
):
    """GET /meal-types includes correct meal_count."""
    # Create a meal associated with this type
    meal = Meal(id=uuid4(), user_id=test_user.id, name=f"Test Meal {uuid4().hex[:8]}", portion_description="Test")
    db.add(meal)
    await db.flush()
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id, meal_type_id=sample_meal_type.id
        )
    )
    await db.flush()

    response = await client.get("/api/v1/meal-types")
    data = response.json()
    mt = next((t for t in data if t["id"] == str(sample_meal_type.id)), None)
    assert mt is not None
    assert mt["meal_count"] == 1


# =============================================================================
# GET /api/v1/meal-types/{id} - Get single meal type
# =============================================================================


@pytest.mark.asyncio
async def test_get_meal_type_by_id(client: AsyncClient, sample_meal_type: MealType):
    """GET /meal-types/{id} returns full meal type detail."""
    response = await client.get(f"/api/v1/meal-types/{sample_meal_type.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_meal_type.id)
    assert data["name"] == sample_meal_type.name
    assert data["description"] == "Morning meal"
    assert data["tags"] == ["morning", "energy"]
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_meal_type_not_found(client: AsyncClient):
    """GET /meal-types/{id} returns 404 for non-existent type."""
    response = await client.get(f"/api/v1/meal-types/{uuid4()}")
    assert response.status_code == 404


# =============================================================================
# POST /api/v1/meal-types - Create meal type
# =============================================================================


@pytest.mark.asyncio
async def test_create_meal_type(client: AsyncClient):
    """POST /meal-types creates a new meal type."""
    payload = {
        "name": f"New Type {uuid4().hex[:8]}",
        "description": "Test description",
        "tags": ["test", "new"],
    }
    response = await client.post("/api/v1/meal-types", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == "Test description"
    assert data["tags"] == ["test", "new"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_meal_type_minimal(client: AsyncClient):
    """POST /meal-types creates meal type with only required fields."""
    payload = {"name": f"Minimal Type {uuid4().hex[:8]}"}
    response = await client.post("/api/v1/meal-types", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] is None
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_create_meal_type_missing_name(client: AsyncClient):
    """POST /meal-types returns 422 when name is missing."""
    response = await client.post("/api/v1/meal-types", json={})
    assert response.status_code == 422


# =============================================================================
# PUT /api/v1/meal-types/{id} - Update meal type
# =============================================================================


@pytest.mark.asyncio
async def test_update_meal_type_name(client: AsyncClient, sample_meal_type: MealType):
    """PUT /meal-types/{id} updates only provided fields."""
    new_name = f"Updated Type {uuid4().hex[:8]}"
    response = await client.put(
        f"/api/v1/meal-types/{sample_meal_type.id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert data["description"] == "Morning meal"  # unchanged


@pytest.mark.asyncio
async def test_update_meal_type_tags(client: AsyncClient, sample_meal_type: MealType):
    """PUT /meal-types/{id} updates tags."""
    response = await client.put(
        f"/api/v1/meal-types/{sample_meal_type.id}",
        json={"tags": ["updated"]},
    )
    assert response.status_code == 200
    assert response.json()["tags"] == ["updated"]


@pytest.mark.asyncio
async def test_update_meal_type_not_found(client: AsyncClient):
    """PUT /meal-types/{id} returns 404 for non-existent type."""
    response = await client.put(
        f"/api/v1/meal-types/{uuid4()}",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


# =============================================================================
# DELETE /api/v1/meal-types/{id} - Delete meal type
# =============================================================================


@pytest.mark.asyncio
async def test_delete_meal_type(client: AsyncClient, sample_meal_type: MealType):
    """DELETE /meal-types/{id} removes the meal type."""
    response = await client.delete(f"/api/v1/meal-types/{sample_meal_type.id}")
    assert response.status_code == 204

    # Confirm it's gone
    response = await client.get(f"/api/v1/meal-types/{sample_meal_type.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_meal_type_not_found(client: AsyncClient):
    """DELETE /meal-types/{id} returns 404 for non-existent type."""
    response = await client.delete(f"/api/v1/meal-types/{uuid4()}")
    assert response.status_code == 404
