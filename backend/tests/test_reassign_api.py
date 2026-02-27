"""
Integration tests for the slot reassignment endpoint (ADR-011).

Tests cover:
- PUT /api/v1/slots/{slot_id}/reassign - Reassign a slot's meal
  - Successful reassignment (same meal type)
  - Reassignment with meal type change
  - Reassignment clears completion status
  - Validation: meal doesn't belong to meal type
  - Validation: slot doesn't exist
  - Validation: past date slot
  - is_manual_override is set
  - Round-robin state is NOT affected
"""
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import delete

from app.main import app
from app.models import (
    DayTemplate,
    DayTemplateSlot,
    Meal,
    MealType,
    WeekPlan,
    WeeklyPlanInstance,
    WeeklyPlanInstanceDay,
    WeeklyPlanSlot,
    RoundRobinState,
)
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
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


def get_week_start(target_date: date) -> date:
    """Get the Monday of the week containing the target date."""
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


@pytest_asyncio.fixture
async def meal_type_a(db: AsyncSession) -> MealType:
    """Create meal type A (e.g., Breakfast)."""
    mt = MealType(
        id=uuid4(),
        name=f"Reassign Breakfast {uuid4().hex[:8]}",
        description="Test meal type A",
    )
    db.add(mt)
    await db.flush()
    return mt


@pytest_asyncio.fixture
async def meal_type_b(db: AsyncSession) -> MealType:
    """Create meal type B (e.g., Lunch)."""
    mt = MealType(
        id=uuid4(),
        name=f"Reassign Lunch {uuid4().hex[:8]}",
        description="Test meal type B",
    )
    db.add(mt)
    await db.flush()
    return mt


@pytest_asyncio.fixture
async def meal_a1(db: AsyncSession, meal_type_a: MealType) -> Meal:
    """Create a meal assigned to meal type A."""
    meal = Meal(
        id=uuid4(),
        name=f"Scrambled Eggs {uuid4().hex[:8]}",
        portion_description="2 eggs + toast",
        calories_kcal=320,
        protein_g=18.5,
        created_at=datetime.now(timezone.utc),
    )
    db.add(meal)
    await db.flush()
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id, meal_type_id=meal_type_a.id
        )
    )
    await db.flush()
    return meal


@pytest_asyncio.fixture
async def meal_a2(db: AsyncSession, meal_type_a: MealType) -> Meal:
    """Create a second meal assigned to meal type A."""
    meal = Meal(
        id=uuid4(),
        name=f"Oatmeal {uuid4().hex[:8]}",
        portion_description="1 cup oats + banana",
        calories_kcal=350,
        protein_g=12.0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(meal)
    await db.flush()
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id, meal_type_id=meal_type_a.id
        )
    )
    await db.flush()
    return meal


@pytest_asyncio.fixture
async def meal_b1(db: AsyncSession, meal_type_b: MealType) -> Meal:
    """Create a meal assigned to meal type B."""
    meal = Meal(
        id=uuid4(),
        name=f"Chicken Salad {uuid4().hex[:8]}",
        portion_description="200g chicken + greens",
        calories_kcal=450,
        protein_g=35.0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(meal)
    await db.flush()
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id, meal_type_id=meal_type_b.id
        )
    )
    await db.flush()
    return meal


@pytest_asyncio.fixture
async def today_slot(
    db: AsyncSession,
    meal_type_a: MealType,
    meal_a1: Meal,
) -> WeeklyPlanSlot:
    """Create a weekly plan with a slot for today."""
    today = date.today()
    week_start = get_week_start(today)

    # Clear any seed data instance for this week to avoid unique constraint violation
    await db.execute(
        delete(WeeklyPlanInstance).where(WeeklyPlanInstance.week_start_date == week_start)
    )
    await db.flush()

    week_plan = WeekPlan(
        id=uuid4(),
        name=f"Test Week {uuid4().hex[:8]}",
        is_default=True,
    )
    db.add(week_plan)
    await db.flush()

    template = DayTemplate(
        id=uuid4(),
        name=f"Test Template {uuid4().hex[:8]}",
    )
    db.add(template)
    await db.flush()

    instance = WeeklyPlanInstance(
        id=uuid4(),
        week_plan_id=week_plan.id,
        week_start_date=week_start,
    )
    db.add(instance)
    await db.flush()

    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        day_template_id=template.id,
        is_override=False,
    )
    db.add(instance_day)
    await db.flush()

    slot = WeeklyPlanSlot(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        position=0,
        meal_type_id=meal_type_a.id,
        meal_id=meal_a1.id,
    )
    db.add(slot)
    await db.flush()
    return slot


class TestReassignSlot:
    """Tests for PUT /api/v1/slots/{slot_id}/reassign endpoint."""

    @pytest.mark.asyncio
    async def test_reassign_same_meal_type(
        self,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
        meal_a2: Meal,
    ):
        """Successfully reassign a slot to a different meal of the same type."""
        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={"meal_id": str(meal_a2.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meal"]["name"] == meal_a2.name
        assert data["is_manual_override"] is True

    @pytest.mark.asyncio
    async def test_reassign_with_meal_type_change(
        self,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
        meal_b1: Meal,
        meal_type_b: MealType,
    ):
        """Successfully reassign with a different meal type."""
        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={
                "meal_id": str(meal_b1.id),
                "meal_type_id": str(meal_type_b.id),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["meal"]["name"] == meal_b1.name
        assert data["meal_type"]["id"] == str(meal_type_b.id)
        assert data["is_manual_override"] is True

    @pytest.mark.asyncio
    async def test_reassign_clears_completion(
        self,
        db: AsyncSession,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
        meal_a2: Meal,
    ):
        """Reassigning a completed slot clears its completion status."""
        # First complete the slot
        today_slot.completion_status = "followed"
        today_slot.completed_at = datetime.now(timezone.utc)
        await db.flush()

        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={"meal_id": str(meal_a2.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["completion_status"] is None
        assert data["completed_at"] is None
        assert data["is_manual_override"] is True

    @pytest.mark.asyncio
    async def test_reassign_meal_type_mismatch(
        self,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
        meal_b1: Meal,
    ):
        """Returns 400 when meal doesn't belong to the slot's meal type."""
        # meal_b1 belongs to meal_type_b, but today_slot uses meal_type_a
        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={"meal_id": str(meal_b1.id)},
        )

        assert response.status_code == 400
        data = response.json()
        assert "meal type" in data["detail"]["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_reassign_slot_not_found(self, client: AsyncClient, meal_a1: Meal):
        """Returns 404 when slot doesn't exist."""
        fake_id = uuid4()
        response = await client.put(
            f"/api/v1/slots/{fake_id}/reassign",
            json={"meal_id": str(meal_a1.id)},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reassign_meal_not_found(
        self,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
    ):
        """Returns 404 when the target meal doesn't exist."""
        fake_meal_id = uuid4()
        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={"meal_id": str(fake_meal_id)},
        )

        assert response.status_code == 404
        data = response.json()
        assert "meal" in data["detail"]["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_reassign_past_date_rejected(
        self,
        db: AsyncSession,
        client: AsyncClient,
        meal_type_a: MealType,
        meal_a1: Meal,
        meal_a2: Meal,
    ):
        """Returns 400 when trying to reassign a past-date slot."""
        yesterday = date.today() - timedelta(days=1)
        week_start = get_week_start(yesterday)

        # Clear seed data instance for this week
        await db.execute(
            delete(WeeklyPlanInstance).where(WeeklyPlanInstance.week_start_date == week_start)
        )
        await db.flush()

        week_plan = WeekPlan(
            id=uuid4(),
            name=f"Test Past {uuid4().hex[:8]}",
            is_default=True,
        )
        db.add(week_plan)
        await db.flush()

        template = DayTemplate(
            id=uuid4(),
            name=f"Test Template Past {uuid4().hex[:8]}",
        )
        db.add(template)
        await db.flush()

        instance = WeeklyPlanInstance(
            id=uuid4(),
            week_plan_id=week_plan.id,
            week_start_date=week_start,
        )
        db.add(instance)
        await db.flush()

        instance_day = WeeklyPlanInstanceDay(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=yesterday,
            day_template_id=template.id,
            is_override=False,
        )
        db.add(instance_day)
        await db.flush()

        past_slot = WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=yesterday,
            position=0,
            meal_type_id=meal_type_a.id,
            meal_id=meal_a1.id,
        )
        db.add(past_slot)
        await db.flush()

        response = await client.put(
            f"/api/v1/slots/{past_slot.id}/reassign",
            json={"meal_id": str(meal_a2.id)},
        )

        assert response.status_code == 400
        data = response.json()
        assert "past" in data["detail"]["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_reassign_does_not_affect_round_robin(
        self,
        db: AsyncSession,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
        meal_type_a: MealType,
        meal_a2: Meal,
    ):
        """Round-robin state should NOT be advanced by reassignment."""
        # Set up round-robin state
        rr_state = RoundRobinState(
            meal_type_id=meal_type_a.id,
            last_meal_id=today_slot.meal_id,
        )
        db.add(rr_state)
        await db.flush()

        original_last_meal_id = rr_state.last_meal_id

        # Reassign the slot
        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={"meal_id": str(meal_a2.id)},
        )
        assert response.status_code == 200

        # Verify round-robin state unchanged
        stmt = select(RoundRobinState).where(
            RoundRobinState.meal_type_id == meal_type_a.id
        )
        result = await db.execute(stmt)
        rr = result.scalar_one()
        assert rr.last_meal_id == original_last_meal_id

    @pytest.mark.asyncio
    async def test_reassign_preserves_slot_metadata(
        self,
        client: AsyncClient,
        today_slot: WeeklyPlanSlot,
        meal_a2: Meal,
    ):
        """Reassignment preserves position, date, and other slot fields."""
        response = await client.put(
            f"/api/v1/slots/{today_slot.id}/reassign",
            json={"meal_id": str(meal_a2.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(today_slot.id)
        assert data["position"] == today_slot.position
        assert data["is_adhoc"] == today_slot.is_adhoc
