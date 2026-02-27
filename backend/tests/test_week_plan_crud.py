"""
Integration tests for the Week Plan CRUD API endpoints.

Tests cover:
- GET /api/v1/week-plans - List week plans with day counts
- GET /api/v1/week-plans/{id} - Get single week plan with days
- POST /api/v1/week-plans - Create week plan with day mappings
- PUT /api/v1/week-plans/{id} - Update week plan and day mappings
- DELETE /api/v1/week-plans/{id} - Delete week plan
- POST /api/v1/week-plans/{id}/set-default - Set as default
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import MealType, DayTemplate, DayTemplateSlot, User, WeekPlan, WeekPlanDay
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
async def sample_templates(db: AsyncSession, test_user: User) -> list[DayTemplate]:
    """Create sample day templates for week plan assignments."""
    suffix = uuid4().hex[:8]
    # Need meal types for the templates
    mt = MealType(id=uuid4(), user_id=test_user.id, name=f"Breakfast {suffix}")
    db.add(mt)

    templates = []
    for name in ["Normal Workday", "Weekend", "Workout Day"]:
        template = DayTemplate(
            id=uuid4(),
            user_id=test_user.id,
            name=f"{name} {suffix}",
        )
        db.add(template)
        templates.append(template)
    await db.flush()
    return templates


@pytest_asyncio.fixture
async def sample_week_plan(
    db: AsyncSession, test_user: User, sample_templates: list[DayTemplate]
) -> WeekPlan:
    """Create a sample week plan with day mappings."""
    plan = WeekPlan(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Standard Week {uuid4().hex[:8]}",
        is_default=False,
    )
    db.add(plan)
    await db.flush()

    # Map Mon-Fri to Normal Workday, Sat-Sun to Weekend
    for weekday in range(5):
        day = WeekPlanDay(
            id=uuid4(),
            week_plan_id=plan.id,
            weekday=weekday,
            day_template_id=sample_templates[0].id,
        )
        db.add(day)
    for weekday in [5, 6]:
        day = WeekPlanDay(
            id=uuid4(),
            week_plan_id=plan.id,
            weekday=weekday,
            day_template_id=sample_templates[1].id,
        )
        db.add(day)
    await db.flush()
    return plan


# =============================================================================
# GET /api/v1/week-plans - List week plans
# =============================================================================


@pytest.mark.asyncio
async def test_list_week_plans(client: AsyncClient, sample_week_plan: WeekPlan):
    """GET /week-plans returns list with day counts."""
    response = await client.get("/api/v1/week-plans")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    plan = next((p for p in data if p["id"] == str(sample_week_plan.id)), None)
    assert plan is not None
    assert plan["name"] == sample_week_plan.name
    assert plan["day_count"] == 7
    assert plan["is_default"] is False


# =============================================================================
# GET /api/v1/week-plans/{id} - Get single week plan
# =============================================================================


@pytest.mark.asyncio
async def test_get_week_plan_by_id(
    client: AsyncClient,
    sample_week_plan: WeekPlan,
    sample_templates: list[DayTemplate],
):
    """GET /week-plans/{id} returns plan with full day mapping details."""
    response = await client.get(f"/api/v1/week-plans/{sample_week_plan.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_week_plan.id)
    assert data["name"] == sample_week_plan.name
    assert len(data["days"]) == 7
    # Days should be ordered by weekday
    weekdays = [d["weekday"] for d in data["days"]]
    assert weekdays == [0, 1, 2, 3, 4, 5, 6]
    # Each day has template info
    assert "day_template" in data["days"][0]
    assert "weekday_name" in data["days"][0]
    assert data["days"][0]["weekday_name"] == "Monday"


@pytest.mark.asyncio
async def test_get_week_plan_not_found(client: AsyncClient):
    """GET /week-plans/{id} returns 404 for non-existent plan."""
    response = await client.get(f"/api/v1/week-plans/{uuid4()}")
    assert response.status_code == 404


# =============================================================================
# POST /api/v1/week-plans - Create week plan
# =============================================================================


@pytest.mark.asyncio
async def test_create_week_plan(
    client: AsyncClient, sample_templates: list[DayTemplate]
):
    """POST /week-plans creates a plan with day mappings."""
    payload = {
        "name": f"New Plan {uuid4().hex[:8]}",
        "is_default": False,
        "days": [
            {"weekday": 0, "day_template_id": str(sample_templates[0].id)},
            {"weekday": 1, "day_template_id": str(sample_templates[0].id)},
            {"weekday": 5, "day_template_id": str(sample_templates[1].id)},
            {"weekday": 6, "day_template_id": str(sample_templates[1].id)},
        ],
    }
    response = await client.post("/api/v1/week-plans", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["is_default"] is False
    assert len(data["days"]) == 4


@pytest.mark.asyncio
async def test_create_week_plan_empty_days(client: AsyncClient):
    """POST /week-plans creates plan without day mappings."""
    payload = {"name": f"Empty Plan {uuid4().hex[:8]}"}
    response = await client.post("/api/v1/week-plans", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["days"] == []


@pytest.mark.asyncio
async def test_create_week_plan_missing_name(client: AsyncClient):
    """POST /week-plans returns 422 when name is missing."""
    response = await client.post("/api/v1/week-plans", json={})
    assert response.status_code == 422


# =============================================================================
# PUT /api/v1/week-plans/{id} - Update week plan
# =============================================================================


@pytest.mark.asyncio
async def test_update_week_plan_name(
    client: AsyncClient, sample_week_plan: WeekPlan
):
    """PUT /week-plans/{id} updates name without touching days."""
    new_name = f"Updated Plan {uuid4().hex[:8]}"
    response = await client.put(
        f"/api/v1/week-plans/{sample_week_plan.id}",
        json={"name": new_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_name
    assert len(data["days"]) == 7  # days unchanged


@pytest.mark.asyncio
async def test_update_week_plan_days(
    client: AsyncClient,
    sample_week_plan: WeekPlan,
    sample_templates: list[DayTemplate],
):
    """PUT /week-plans/{id} with days replaces all day mappings."""
    response = await client.put(
        f"/api/v1/week-plans/{sample_week_plan.id}",
        json={
            "days": [
                {"weekday": 0, "day_template_id": str(sample_templates[2].id)},
            ]
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["days"]) == 1  # replaced 7 days with 1
    assert data["days"][0]["weekday"] == 0
    assert data["days"][0]["day_template"]["id"] == str(sample_templates[2].id)


@pytest.mark.asyncio
async def test_update_week_plan_not_found(client: AsyncClient):
    """PUT /week-plans/{id} returns 404 for non-existent plan."""
    response = await client.put(
        f"/api/v1/week-plans/{uuid4()}",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


# =============================================================================
# DELETE /api/v1/week-plans/{id} - Delete week plan
# =============================================================================


@pytest.mark.asyncio
async def test_delete_week_plan(client: AsyncClient, db: AsyncSession, test_user: User):
    """DELETE /week-plans/{id} removes the plan."""
    plan = WeekPlan(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Deletable Plan {uuid4().hex[:8]}",
    )
    db.add(plan)
    await db.flush()

    response = await client.delete(f"/api/v1/week-plans/{plan.id}")
    assert response.status_code == 204

    # Confirm it's gone
    response = await client.get(f"/api/v1/week-plans/{plan.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_week_plan_not_found(client: AsyncClient):
    """DELETE /week-plans/{id} returns 404 for non-existent plan."""
    response = await client.delete(f"/api/v1/week-plans/{uuid4()}")
    assert response.status_code == 404


# =============================================================================
# POST /api/v1/week-plans/{id}/set-default - Set as default
# =============================================================================


@pytest.mark.asyncio
async def test_set_default_week_plan(
    client: AsyncClient, sample_week_plan: WeekPlan
):
    """POST /week-plans/{id}/set-default marks plan as default."""
    response = await client.post(
        f"/api/v1/week-plans/{sample_week_plan.id}/set-default"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True


@pytest.mark.asyncio
async def test_set_default_clears_previous(
    client: AsyncClient, db: AsyncSession, test_user: User, sample_templates: list[DayTemplate]
):
    """POST /week-plans/{id}/set-default clears previous default."""
    # Create two plans
    plan1 = WeekPlan(id=uuid4(), user_id=test_user.id, name=f"Plan A {uuid4().hex[:8]}", is_default=True)
    plan2 = WeekPlan(id=uuid4(), user_id=test_user.id, name=f"Plan B {uuid4().hex[:8]}", is_default=False)
    db.add(plan1)
    db.add(plan2)
    await db.flush()

    # Set plan2 as default
    response = await client.post(f"/api/v1/week-plans/{plan2.id}/set-default")
    assert response.status_code == 200
    assert response.json()["is_default"] is True

    # Verify plan1 is no longer default
    response = await client.get(f"/api/v1/week-plans/{plan1.id}")
    assert response.json()["is_default"] is False


@pytest.mark.asyncio
async def test_set_default_not_found(client: AsyncClient):
    """POST /week-plans/{id}/set-default returns 404 for non-existent plan."""
    response = await client.post(f"/api/v1/week-plans/{uuid4()}/set-default")
    assert response.status_code == 404
