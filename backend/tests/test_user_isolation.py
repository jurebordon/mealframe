"""
Cross-user isolation tests (ADR-014 session 3).

Verifies that authenticated users cannot see or modify data belonging to other users.
Each test creates data for user_a and user_b, then verifies that requests
authenticated as user_a cannot access user_b's resources (and vice versa).

Note: Because FastAPI dependency_overrides is global, we must switch the
override between user_a and user_b within each test rather than using
two concurrent client fixtures.
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import (
    DayTemplate,
    DayTemplateSlot,
    Meal,
    MealType,
    User,
    WeekPlan,
    WeekPlanDay,
)
from app.models.meal_to_meal_type import meal_to_meal_type
from app.database import get_db
from app.dependencies import get_current_user


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user_a(db: AsyncSession) -> User:
    """Create user A."""
    user = User(
        id=uuid4(),
        email=f"user_a_{uuid4().hex[:8]}@test.io",
        email_verified=True,
        is_active=True,
        auth_provider="email",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def user_b(db: AsyncSession) -> User:
    """Create user B."""
    user = User(
        id=uuid4(),
        email=f"user_b_{uuid4().hex[:8]}@test.io",
        email_verified=True,
        is_active=True,
        auth_provider="email",
    )
    db.add(user)
    await db.flush()
    return user


async def _client_for(db: AsyncSession, user: User) -> AsyncClient:
    """Create an AsyncClient authenticated as the given user."""

    async def override_get_db():
        yield db

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


# ---------------------------------------------------------------------------
# Meal type isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_meal_types_isolated(
    db: AsyncSession, user_a: User, user_b: User
):
    """User A's meal types are invisible to user B."""
    mt_a = MealType(id=uuid4(), user_id=user_a.id, name=f"A-Breakfast-{uuid4().hex[:6]}")
    mt_b = MealType(id=uuid4(), user_id=user_b.id, name=f"B-Breakfast-{uuid4().hex[:6]}")
    db.add(mt_a)
    db.add(mt_b)
    await db.flush()

    # User A sees only their meal type
    async with await _client_for(db, user_a) as client_a:
        resp_a = await client_a.get("/api/v1/meal-types")
        assert resp_a.status_code == 200
        names_a = [mt["name"] for mt in resp_a.json()]
        assert mt_a.name in names_a
        assert mt_b.name not in names_a

    # User B sees only their meal type
    async with await _client_for(db, user_b) as client_b:
        resp_b = await client_b.get("/api/v1/meal-types")
        assert resp_b.status_code == 200
        names_b = [mt["name"] for mt in resp_b.json()]
        assert mt_b.name in names_b
        assert mt_a.name not in names_b

    # User A cannot GET user B's meal type by ID
    async with await _client_for(db, user_a) as client_a:
        resp_cross = await client_a.get(f"/api/v1/meal-types/{mt_b.id}")
        assert resp_cross.status_code == 404

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Meal isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_meals_isolated(
    db: AsyncSession, user_a: User, user_b: User
):
    """User A's meals are invisible to user B."""
    meal_a = Meal(
        id=uuid4(), user_id=user_a.id,
        name=f"A-Oatmeal-{uuid4().hex[:6]}", portion_description="100g"
    )
    meal_b = Meal(
        id=uuid4(), user_id=user_b.id,
        name=f"B-Oatmeal-{uuid4().hex[:6]}", portion_description="100g"
    )
    db.add(meal_a)
    db.add(meal_b)
    await db.flush()

    # User A list excludes B's meal
    async with await _client_for(db, user_a) as client_a:
        resp_a = await client_a.get("/api/v1/meals")
        assert resp_a.status_code == 200
        ids_a = [m["id"] for m in resp_a.json()["items"]]
        assert str(meal_a.id) in ids_a
        assert str(meal_b.id) not in ids_a

    # User A cannot GET user B's meal
    async with await _client_for(db, user_a) as client_a:
        resp_cross = await client_a.get(f"/api/v1/meals/{meal_b.id}")
        assert resp_cross.status_code == 404

    # User A cannot UPDATE user B's meal
    async with await _client_for(db, user_a) as client_a:
        resp_update = await client_a.put(
            f"/api/v1/meals/{meal_b.id}",
            json={"name": "Hacked"},
        )
        assert resp_update.status_code == 404

    # User A cannot DELETE user B's meal
    async with await _client_for(db, user_a) as client_a:
        resp_delete = await client_a.delete(f"/api/v1/meals/{meal_b.id}")
        assert resp_delete.status_code == 404

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Day template isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_day_templates_isolated(
    db: AsyncSession, user_a: User, user_b: User
):
    """User A's day templates are invisible to user B."""
    mt_a = MealType(id=uuid4(), user_id=user_a.id, name=f"A-MT-{uuid4().hex[:6]}")
    db.add(mt_a)
    await db.flush()

    dt_a = DayTemplate(id=uuid4(), user_id=user_a.id, name=f"A-Template-{uuid4().hex[:6]}")
    db.add(dt_a)
    await db.flush()

    slot = DayTemplateSlot(id=uuid4(), day_template_id=dt_a.id, meal_type_id=mt_a.id, position=0)
    db.add(slot)
    await db.flush()

    # User B cannot see user A's template in list
    async with await _client_for(db, user_b) as client_b:
        resp_list = await client_b.get("/api/v1/day-templates")
        assert resp_list.status_code == 200
        ids = [t["id"] for t in resp_list.json()]
        assert str(dt_a.id) not in ids

    # User B cannot GET user A's template by ID
    async with await _client_for(db, user_b) as client_b:
        resp_get = await client_b.get(f"/api/v1/day-templates/{dt_a.id}")
        assert resp_get.status_code == 404

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Week plan isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_week_plans_isolated(
    db: AsyncSession, user_a: User, user_b: User
):
    """User A's week plans are invisible to user B."""
    mt = MealType(id=uuid4(), user_id=user_a.id, name=f"A-MT-{uuid4().hex[:6]}")
    db.add(mt)
    await db.flush()

    dt = DayTemplate(id=uuid4(), user_id=user_a.id, name=f"A-DT-{uuid4().hex[:6]}")
    db.add(dt)
    await db.flush()

    slot = DayTemplateSlot(id=uuid4(), day_template_id=dt.id, meal_type_id=mt.id, position=0)
    db.add(slot)
    await db.flush()

    wp = WeekPlan(id=uuid4(), user_id=user_a.id, name=f"A-WeekPlan-{uuid4().hex[:6]}", is_default=False)
    db.add(wp)
    await db.flush()

    day = WeekPlanDay(id=uuid4(), week_plan_id=wp.id, weekday=0, day_template_id=dt.id)
    db.add(day)
    await db.flush()

    # User B cannot see user A's week plan in list
    async with await _client_for(db, user_b) as client_b:
        resp_list = await client_b.get("/api/v1/week-plans")
        assert resp_list.status_code == 200
        ids = [p["id"] for p in resp_list.json()]
        assert str(wp.id) not in ids

    # User B cannot GET user A's week plan by ID
    async with await _client_for(db, user_b) as client_b:
        resp_get = await client_b.get(f"/api/v1/week-plans/{wp.id}")
        assert resp_get.status_code == 404

    # User B cannot DELETE user A's week plan
    async with await _client_for(db, user_b) as client_b:
        resp_delete = await client_b.delete(f"/api/v1/week-plans/{wp.id}")
        assert resp_delete.status_code == 404

    app.dependency_overrides.clear()
