"""
Integration tests for the Day Template CRUD API endpoints.

Tests cover:
- GET /api/v1/day-templates - List templates with slot info
- GET /api/v1/day-templates/{id} - Get single template with slots
- POST /api/v1/day-templates - Create template with slots
- PUT /api/v1/day-templates/{id} - Update template and slots
- DELETE /api/v1/day-templates/{id} - Delete template
"""
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import MealType, DayTemplate, DayTemplateSlot, User
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
    """Create sample meal types for slot assignments."""
    suffix = uuid4().hex[:8]
    types = []
    for name in ["Breakfast", "Lunch", "Dinner"]:
        mt = MealType(id=uuid4(), user_id=test_user.id, name=f"{name} {suffix}", description=f"Test {name}")
        db.add(mt)
        types.append(mt)
    await db.flush()
    return types


@pytest_asyncio.fixture
async def sample_template(
    db: AsyncSession, test_user: User, sample_meal_types: list[MealType]
) -> DayTemplate:
    """Create a sample day template with slots."""
    template = DayTemplate(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Normal Workday {uuid4().hex[:8]}",
        notes="Standard workday template",
    )
    db.add(template)
    await db.flush()

    for i, mt in enumerate(sample_meal_types):
        slot = DayTemplateSlot(
            id=uuid4(),
            day_template_id=template.id,
            position=i + 1,
            meal_type_id=mt.id,
        )
        db.add(slot)
    await db.flush()
    return template


# =============================================================================
# GET /api/v1/day-templates - List templates
# =============================================================================


@pytest.mark.asyncio
async def test_list_day_templates(
    client: AsyncClient, sample_template: DayTemplate, sample_meal_types: list[MealType]
):
    """GET /day-templates returns list with slot counts and previews."""
    response = await client.get("/api/v1/day-templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Find our sample template
    tmpl = next((t for t in data if t["id"] == str(sample_template.id)), None)
    assert tmpl is not None
    assert tmpl["name"] == sample_template.name
    assert tmpl["slot_count"] == 3
    assert " → " in tmpl["slot_preview"]


# =============================================================================
# GET /api/v1/day-templates/{id} - Get single template
# =============================================================================


@pytest.mark.asyncio
async def test_get_day_template_by_id(
    client: AsyncClient, sample_template: DayTemplate, sample_meal_types: list[MealType]
):
    """GET /day-templates/{id} returns template with full slot details."""
    response = await client.get(f"/api/v1/day-templates/{sample_template.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_template.id)
    assert data["name"] == sample_template.name
    assert data["notes"] == "Standard workday template"
    assert len(data["slots"]) == 3
    # Check slots are ordered
    assert data["slots"][0]["position"] == 1
    assert data["slots"][1]["position"] == 2
    assert data["slots"][2]["position"] == 3
    # Check slot has meal type info
    assert "meal_type" in data["slots"][0]
    assert "id" in data["slots"][0]["meal_type"]
    assert "name" in data["slots"][0]["meal_type"]


@pytest.mark.asyncio
async def test_get_day_template_not_found(client: AsyncClient):
    """GET /day-templates/{id} returns 404 for non-existent template."""
    response = await client.get(f"/api/v1/day-templates/{uuid4()}")
    assert response.status_code == 404


# =============================================================================
# POST /api/v1/day-templates - Create template
# =============================================================================


@pytest.mark.asyncio
async def test_create_day_template(
    client: AsyncClient, sample_meal_types: list[MealType]
):
    """POST /day-templates creates template with slots."""
    payload = {
        "name": f"New Template {uuid4().hex[:8]}",
        "notes": "Test notes",
        "slots": [
            {"position": 1, "meal_type_id": str(sample_meal_types[0].id)},
            {"position": 2, "meal_type_id": str(sample_meal_types[1].id)},
        ],
    }
    response = await client.post("/api/v1/day-templates", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["notes"] == "Test notes"
    assert len(data["slots"]) == 2
    assert data["slots"][0]["position"] == 1
    assert data["slots"][0]["meal_type"]["id"] == str(sample_meal_types[0].id)


@pytest.mark.asyncio
async def test_create_day_template_no_slots(client: AsyncClient):
    """POST /day-templates creates template without slots."""
    payload = {"name": f"Empty Template {uuid4().hex[:8]}"}
    response = await client.post("/api/v1/day-templates", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["slots"] == []


@pytest.mark.asyncio
async def test_create_day_template_missing_name(client: AsyncClient):
    """POST /day-templates returns 422 when name is missing."""
    response = await client.post("/api/v1/day-templates", json={})
    assert response.status_code == 422


# =============================================================================
# PUT /api/v1/day-templates/{id} - Update template
# =============================================================================


@pytest.mark.asyncio
async def test_update_day_template_name(
    client: AsyncClient, sample_template: DayTemplate
):
    """PUT /day-templates/{id} updates name without touching slots."""
    new_name = f"Updated Template {uuid4().hex[:8]}"
    response = await client.put(
        f"/api/v1/day-templates/{sample_template.id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert len(data["slots"]) == 3  # slots unchanged


@pytest.mark.asyncio
async def test_update_day_template_slots(
    client: AsyncClient,
    sample_template: DayTemplate,
    sample_meal_types: list[MealType],
):
    """PUT /day-templates/{id} with slots replaces all slots."""
    response = await client.put(
        f"/api/v1/day-templates/{sample_template.id}",
        json={
            "slots": [
                {"position": 1, "meal_type_id": str(sample_meal_types[2].id)},
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["slots"]) == 1  # replaced 3 slots with 1
    assert data["slots"][0]["meal_type"]["id"] == str(sample_meal_types[2].id)


@pytest.mark.asyncio
async def test_update_day_template_not_found(client: AsyncClient):
    """PUT /day-templates/{id} returns 404 for non-existent template."""
    response = await client.put(
        f"/api/v1/day-templates/{uuid4()}",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


# =============================================================================
# DELETE /api/v1/day-templates/{id} - Delete template
# =============================================================================


@pytest.mark.asyncio
async def test_delete_day_template(client: AsyncClient, db: AsyncSession, test_user: User):
    """DELETE /day-templates/{id} removes the template."""
    # Create a standalone template (not used by any week plan)
    template = DayTemplate(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Deletable Template {uuid4().hex[:8]}",
    )
    db.add(template)
    await db.flush()

    response = await client.delete(f"/api/v1/day-templates/{template.id}")
    assert response.status_code == 204

    # Confirm it's gone
    response = await client.get(f"/api/v1/day-templates/{template.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_day_template_not_found(client: AsyncClient):
    """DELETE /day-templates/{id} returns 404 for non-existent template."""
    response = await client.delete(f"/api/v1/day-templates/{uuid4()}")
    assert response.status_code == 404


# =============================================================================
# Soft Limits (max_calories_kcal, max_protein_g)
# =============================================================================


@pytest.mark.asyncio
async def test_create_day_template_with_soft_limits(
    client: AsyncClient, sample_meal_types: list[MealType]
):
    """POST /day-templates creates template with soft limit fields."""
    payload = {
        "name": f"Limited Template {uuid4().hex[:8]}",
        "max_calories_kcal": 2200,
        "max_protein_g": "180.0",
        "slots": [
            {"position": 1, "meal_type_id": str(sample_meal_types[0].id)},
        ],
    }
    response = await client.post("/api/v1/day-templates", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["max_calories_kcal"] == 2200
    assert data["max_protein_g"] == "180.0"


@pytest.mark.asyncio
async def test_create_day_template_without_soft_limits(
    client: AsyncClient, sample_meal_types: list[MealType]
):
    """POST /day-templates without limits returns null for limit fields."""
    payload = {
        "name": f"No Limits {uuid4().hex[:8]}",
        "slots": [
            {"position": 1, "meal_type_id": str(sample_meal_types[0].id)},
        ],
    }
    response = await client.post("/api/v1/day-templates", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["max_calories_kcal"] is None
    assert data["max_protein_g"] is None


@pytest.mark.asyncio
async def test_update_day_template_set_soft_limits(
    client: AsyncClient, sample_template: DayTemplate
):
    """PUT /day-templates/{id} can set soft limits."""
    response = await client.put(
        f"/api/v1/day-templates/{sample_template.id}",
        json={"max_calories_kcal": 1800, "max_protein_g": "150.5"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["max_calories_kcal"] == 1800
    assert data["max_protein_g"] == "150.5"


@pytest.mark.asyncio
async def test_update_day_template_clear_soft_limits(
    client: AsyncClient, db: AsyncSession, test_user: User, sample_meal_types: list[MealType]
):
    """PUT /day-templates/{id} can clear soft limits by sending null."""
    # Create a template with limits
    template = DayTemplate(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Clearable Limits {uuid4().hex[:8]}",
        max_calories_kcal=2000,
        max_protein_g=160,
    )
    db.add(template)
    await db.flush()

    # Clear limits
    response = await client.put(
        f"/api/v1/day-templates/{template.id}",
        json={"max_calories_kcal": None, "max_protein_g": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["max_calories_kcal"] is None
    assert data["max_protein_g"] is None


@pytest.mark.asyncio
async def test_update_day_template_omit_limits_preserves_them(
    client: AsyncClient, db: AsyncSession, test_user: User
):
    """PUT /day-templates/{id} without limit fields leaves them unchanged."""
    template = DayTemplate(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Preserved Limits {uuid4().hex[:8]}",
        max_calories_kcal=2500,
        max_protein_g=200,
    )
    db.add(template)
    await db.flush()

    # Update only name — limits should remain
    new_name = f"Renamed {uuid4().hex[:8]}"
    response = await client.put(
        f"/api/v1/day-templates/{template.id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert data["max_calories_kcal"] == 2500
    assert data["max_protein_g"] == "200.0"


@pytest.mark.asyncio
async def test_list_day_templates_includes_soft_limits(
    client: AsyncClient, db: AsyncSession, test_user: User
):
    """GET /day-templates list includes soft limit fields."""
    template = DayTemplate(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Listed Limits {uuid4().hex[:8]}",
        max_calories_kcal=1900,
        max_protein_g=170,
    )
    db.add(template)
    await db.flush()

    response = await client.get("/api/v1/day-templates")
    assert response.status_code == 200
    data = response.json()

    tmpl = next((t for t in data if t["id"] == str(template.id)), None)
    assert tmpl is not None
    assert tmpl["max_calories_kcal"] == 1900
    assert Decimal(tmpl["max_protein_g"]) == Decimal("170")
