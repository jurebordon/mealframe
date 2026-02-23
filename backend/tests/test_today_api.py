"""
Integration tests for the daily use API endpoints.

Tests cover:
- GET /api/v1/today - Today's meal plan
- GET /api/v1/yesterday - Yesterday's plan
- POST /api/v1/slots/{id}/complete - Mark slot complete
- DELETE /api/v1/slots/{id}/complete - Undo completion

These tests use the database fixtures from conftest.py and create
weekly plan instances with slots for testing.
"""
from datetime import date, datetime, timedelta, timezone
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
    WeekPlan,
    WeekPlanDay,
    WeeklyPlanInstance,
    WeeklyPlanInstanceDay,
    WeeklyPlanSlot,
)
from app.models.meal_to_meal_type import meal_to_meal_type
from app.database import get_db


# Fixture to override database dependency
@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """
    Create an async HTTP client with database override.

    Overrides the get_db dependency to use the test session with rollback.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


# Helper fixtures for creating test data

@pytest_asyncio.fixture
async def test_meal_type(db: AsyncSession) -> MealType:
    """Create a meal type for testing."""
    mt = MealType(
        id=uuid4(),
        name=f"Test Breakfast {uuid4().hex[:8]}",
        description="Test meal type",
    )
    db.add(mt)
    await db.flush()
    return mt


@pytest_asyncio.fixture
async def test_meal(db: AsyncSession, test_meal_type: MealType) -> Meal:
    """Create a meal for testing."""
    meal = Meal(
        id=uuid4(),
        name=f"Test Scrambled Eggs {uuid4().hex[:8]}",
        portion_description="2 eggs + 1 slice toast",
        calories_kcal=320,
        protein_g=18.5,
        carbs_g=15.0,
        fat_g=22.0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(meal)
    await db.flush()

    # Associate meal with meal type
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id,
            meal_type_id=test_meal_type.id,
        )
    )
    await db.flush()
    return meal


@pytest_asyncio.fixture
async def test_day_template(db: AsyncSession, test_meal_type: MealType) -> DayTemplate:
    """Create a day template with one slot."""
    template = DayTemplate(
        id=uuid4(),
        name=f"Test Workday {uuid4().hex[:8]}",
        notes="Test template",
    )
    db.add(template)
    await db.flush()

    slot = DayTemplateSlot(
        id=uuid4(),
        day_template_id=template.id,
        position=1,
        meal_type_id=test_meal_type.id,
    )
    db.add(slot)
    await db.flush()

    return template


def get_week_start(target_date: date) -> date:
    """Get the Monday of the week containing the target date."""
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


@pytest_asyncio.fixture
async def weekly_plan_with_today(
    db: AsyncSession,
    test_meal_type: MealType,
    test_meal: Meal,
    test_day_template: DayTemplate,
) -> tuple[WeeklyPlanInstance, WeeklyPlanSlot]:
    """
    Create a weekly plan instance with a slot for today.

    Returns the instance and the slot for today.
    """
    today = date.today()
    week_start = get_week_start(today)

    # Create week plan
    week_plan = WeekPlan(
        id=uuid4(),
        name=f"Test Week Plan {uuid4().hex[:8]}",
        is_default=True,
    )
    db.add(week_plan)
    await db.flush()

    # Create weekly plan instance
    instance = WeeklyPlanInstance(
        id=uuid4(),
        week_plan_id=week_plan.id,
        week_start_date=week_start,
    )
    db.add(instance)
    await db.flush()

    # Create instance day for today
    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        day_template_id=test_day_template.id,
        is_override=False,
    )
    db.add(instance_day)
    await db.flush()

    # Create slot for today
    slot = WeeklyPlanSlot(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        position=1,
        meal_type_id=test_meal_type.id,
        meal_id=test_meal.id,
        completion_status=None,
        completed_at=None,
    )
    db.add(slot)
    await db.flush()

    return (instance, slot)


@pytest_asyncio.fixture
async def weekly_plan_with_yesterday(
    db: AsyncSession,
    test_meal_type: MealType,
    test_meal: Meal,
    test_day_template: DayTemplate,
) -> tuple[WeeklyPlanInstance, WeeklyPlanSlot]:
    """
    Create a weekly plan instance with a slot for yesterday.

    Returns the instance and the slot for yesterday.
    """
    yesterday = date.today() - timedelta(days=1)
    week_start = get_week_start(yesterday)

    # Create week plan
    week_plan = WeekPlan(
        id=uuid4(),
        name=f"Test Week Plan {uuid4().hex[:8]}",
        is_default=True,
    )
    db.add(week_plan)
    await db.flush()

    # Create weekly plan instance
    instance = WeeklyPlanInstance(
        id=uuid4(),
        week_plan_id=week_plan.id,
        week_start_date=week_start,
    )
    db.add(instance)
    await db.flush()

    # Create instance day for yesterday
    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=yesterday,
        day_template_id=test_day_template.id,
        is_override=False,
    )
    db.add(instance_day)
    await db.flush()

    # Create slot for yesterday
    slot = WeeklyPlanSlot(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=yesterday,
        position=1,
        meal_type_id=test_meal_type.id,
        meal_id=test_meal.id,
        completion_status=None,
        completed_at=None,
    )
    db.add(slot)
    await db.flush()

    return (instance, slot)


class TestGetToday:
    """Tests for GET /api/v1/today endpoint."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_plan(self, client: AsyncClient):
        """When no plan exists for today, returns empty slots list."""
        response = await client.get("/api/v1/today")

        assert response.status_code == 200
        data = response.json()

        assert data["date"] == date.today().isoformat()
        assert data["weekday"] in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert data["template"] is None
        assert data["is_override"] is False
        assert data["slots"] == []
        assert data["stats"]["completed"] == 0
        assert data["stats"]["total"] == 0
        assert data["stats"]["streak_days"] == 0

    @pytest.mark.asyncio
    async def test_returns_today_slots(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
        test_meal: Meal,
        test_meal_type: MealType,
    ):
        """When a plan exists, returns today's slots with meal details."""
        instance, slot = weekly_plan_with_today

        response = await client.get("/api/v1/today")

        assert response.status_code == 200
        data = response.json()

        assert data["date"] == date.today().isoformat()
        assert data["template"] is not None
        assert data["is_override"] is False
        assert len(data["slots"]) == 1

        slot_data = data["slots"][0]
        assert slot_data["id"] == str(slot.id)
        assert slot_data["position"] == 1
        assert slot_data["is_next"] is True  # First incomplete slot
        assert slot_data["completion_status"] is None

        # Check meal details
        assert slot_data["meal"]["name"] == test_meal.name
        assert slot_data["meal"]["portion_description"] == "2 eggs + 1 slice toast"
        assert slot_data["meal"]["calories_kcal"] == 320

        # Check stats
        assert data["stats"]["completed"] == 0
        assert data["stats"]["total"] == 1

    @pytest.mark.asyncio
    async def test_is_next_on_first_incomplete(
        self,
        db: AsyncSession,
        client: AsyncClient,
        test_meal_type: MealType,
        test_meal: Meal,
        test_day_template: DayTemplate,
    ):
        """is_next should be True only for the first incomplete slot."""
        today = date.today()
        week_start = get_week_start(today)

        # Create week plan and instance
        week_plan = WeekPlan(id=uuid4(), name=f"Test {uuid4().hex[:8]}", is_default=True)
        db.add(week_plan)
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
            day_template_id=test_day_template.id,
            is_override=False,
        )
        db.add(instance_day)
        await db.flush()

        # Create 3 slots - first completed, second and third incomplete
        slot1 = WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=today,
            position=1,
            meal_type_id=test_meal_type.id,
            meal_id=test_meal.id,
            completion_status="followed",
            completed_at=datetime.now(timezone.utc),
        )
        slot2 = WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=today,
            position=2,
            meal_type_id=test_meal_type.id,
            meal_id=test_meal.id,
            completion_status=None,
            completed_at=None,
        )
        slot3 = WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=today,
            position=3,
            meal_type_id=test_meal_type.id,
            meal_id=test_meal.id,
            completion_status=None,
            completed_at=None,
        )
        db.add_all([slot1, slot2, slot3])
        await db.flush()

        response = await client.get("/api/v1/today")

        assert response.status_code == 200
        data = response.json()

        assert len(data["slots"]) == 3
        assert data["slots"][0]["is_next"] is False  # Completed
        assert data["slots"][1]["is_next"] is True   # First incomplete
        assert data["slots"][2]["is_next"] is False  # Not first incomplete

        assert data["stats"]["completed"] == 1
        assert data["stats"]["total"] == 3


class TestGetYesterday:
    """Tests for GET /api/v1/yesterday endpoint."""

    @pytest.mark.asyncio
    async def test_returns_yesterday_slots(
        self,
        client: AsyncClient,
        weekly_plan_with_yesterday: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
        test_meal: Meal,
    ):
        """Returns yesterday's slots with meal details."""
        instance, slot = weekly_plan_with_yesterday

        response = await client.get("/api/v1/yesterday")

        assert response.status_code == 200
        data = response.json()

        yesterday = date.today() - timedelta(days=1)
        assert data["date"] == yesterday.isoformat()
        assert len(data["slots"]) == 1
        assert data["slots"][0]["id"] == str(slot.id)


class TestCompleteSlot:
    """Tests for POST /api/v1/slots/{slot_id}/complete endpoint."""

    @pytest.mark.asyncio
    async def test_complete_slot_followed(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Successfully marks a slot as followed."""
        instance, slot = weekly_plan_with_today

        response = await client.post(
            f"/api/v1/slots/{slot.id}/complete",
            json={"status": "followed"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(slot.id)
        assert data["completion_status"] == "followed"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_complete_slot_skipped(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Successfully marks a slot as skipped."""
        instance, slot = weekly_plan_with_today

        response = await client.post(
            f"/api/v1/slots/{slot.id}/complete",
            json={"status": "skipped"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["completion_status"] == "skipped"

    @pytest.mark.asyncio
    async def test_complete_slot_equivalent(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Successfully marks a slot as equivalent."""
        instance, slot = weekly_plan_with_today

        response = await client.post(
            f"/api/v1/slots/{slot.id}/complete",
            json={"status": "equivalent"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["completion_status"] == "equivalent"

    @pytest.mark.asyncio
    async def test_complete_slot_deviated(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Successfully marks a slot as deviated."""
        instance, slot = weekly_plan_with_today

        response = await client.post(
            f"/api/v1/slots/{slot.id}/complete",
            json={"status": "deviated"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["completion_status"] == "deviated"

    @pytest.mark.asyncio
    async def test_complete_slot_social(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Successfully marks a slot as social."""
        instance, slot = weekly_plan_with_today

        response = await client.post(
            f"/api/v1/slots/{slot.id}/complete",
            json={"status": "social"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["completion_status"] == "social"

    @pytest.mark.asyncio
    async def test_complete_slot_not_found(self, client: AsyncClient):
        """Returns 404 when slot doesn't exist."""
        fake_id = uuid4()

        response = await client.post(
            f"/api/v1/slots/{fake_id}/complete",
            json={"status": "followed"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_complete_slot_invalid_status(
        self,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Returns 422 for invalid status value."""
        instance, slot = weekly_plan_with_today

        response = await client.post(
            f"/api/v1/slots/{slot.id}/complete",
            json={"status": "invalid_status"}
        )

        assert response.status_code == 422


class TestUncompleteSlot:
    """Tests for DELETE /api/v1/slots/{slot_id}/complete endpoint."""

    @pytest.mark.asyncio
    async def test_uncomplete_slot(
        self,
        db: AsyncSession,
        client: AsyncClient,
        weekly_plan_with_today: tuple[WeeklyPlanInstance, WeeklyPlanSlot],
    ):
        """Successfully resets a slot to unmarked."""
        instance, slot = weekly_plan_with_today

        # First mark as complete
        slot.completion_status = "followed"
        slot.completed_at = datetime.now(timezone.utc)
        await db.flush()

        # Then uncomplete
        response = await client.delete(f"/api/v1/slots/{slot.id}/complete")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(slot.id)
        assert data["completion_status"] is None
        assert data["completed_at"] is None

    @pytest.mark.asyncio
    async def test_uncomplete_slot_not_found(self, client: AsyncClient):
        """Returns 404 when slot doesn't exist."""
        fake_id = uuid4()

        response = await client.delete(f"/api/v1/slots/{fake_id}/complete")

        assert response.status_code == 404


class TestStreakCalculation:
    """Tests for streak calculation in the stats."""

    @pytest.mark.asyncio
    async def test_streak_with_completed_days(
        self,
        db: AsyncSession,
        client: AsyncClient,
        test_meal_type: MealType,
        test_meal: Meal,
        test_day_template: DayTemplate,
    ):
        """Streak counts consecutive completed days."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)

        # We need yesterday in the same week as today for the week_start to work
        week_start_yesterday = get_week_start(yesterday)
        week_start_day_before = get_week_start(day_before)

        # Create week plan
        week_plan = WeekPlan(id=uuid4(), name=f"Test {uuid4().hex[:8]}", is_default=True)
        db.add(week_plan)
        await db.flush()

        # Create instances for each week that's needed
        instances = {}
        for ws in set([week_start_yesterday, week_start_day_before]):
            instance = WeeklyPlanInstance(
                id=uuid4(),
                week_plan_id=week_plan.id,
                week_start_date=ws,
            )
            db.add(instance)
            await db.flush()
            instances[ws] = instance

        # Create completed days for yesterday and day before
        for check_date in [yesterday, day_before]:
            ws = get_week_start(check_date)
            instance = instances[ws]

            instance_day = WeeklyPlanInstanceDay(
                id=uuid4(),
                weekly_plan_instance_id=instance.id,
                date=check_date,
                day_template_id=test_day_template.id,
                is_override=False,
            )
            db.add(instance_day)
            await db.flush()

            slot = WeeklyPlanSlot(
                id=uuid4(),
                weekly_plan_instance_id=instance.id,
                date=check_date,
                position=1,
                meal_type_id=test_meal_type.id,
                meal_id=test_meal.id,
                completion_status="followed",  # Completed
                completed_at=datetime.now(timezone.utc),
            )
            db.add(slot)
            await db.flush()

        response = await client.get("/api/v1/today")

        assert response.status_code == 200
        data = response.json()

        # Streak should be 2 (yesterday and day before both completed)
        assert data["stats"]["streak_days"] == 2

    @pytest.mark.asyncio
    async def test_streak_breaks_on_incomplete_day(
        self,
        db: AsyncSession,
        client: AsyncClient,
        test_meal_type: MealType,
        test_meal: Meal,
        test_day_template: DayTemplate,
    ):
        """Streak breaks when encountering an incomplete day."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)

        week_start = get_week_start(yesterday)
        week_start_day_before = get_week_start(day_before)

        # Create week plan
        week_plan = WeekPlan(id=uuid4(), name=f"Test {uuid4().hex[:8]}", is_default=True)
        db.add(week_plan)
        await db.flush()

        # Create instances
        instances = {}
        for ws in set([week_start, week_start_day_before]):
            instance = WeeklyPlanInstance(
                id=uuid4(),
                week_plan_id=week_plan.id,
                week_start_date=ws,
            )
            db.add(instance)
            await db.flush()
            instances[ws] = instance

        # Yesterday - incomplete
        instance = instances[week_start]
        instance_day_yesterday = WeeklyPlanInstanceDay(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=yesterday,
            day_template_id=test_day_template.id,
            is_override=False,
        )
        db.add(instance_day_yesterday)
        await db.flush()

        slot_yesterday = WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=yesterday,
            position=1,
            meal_type_id=test_meal_type.id,
            meal_id=test_meal.id,
            completion_status=None,  # Not completed!
            completed_at=None,
        )
        db.add(slot_yesterday)
        await db.flush()

        # Day before yesterday - completed
        instance_before = instances[week_start_day_before]
        instance_day_before = WeeklyPlanInstanceDay(
            id=uuid4(),
            weekly_plan_instance_id=instance_before.id,
            date=day_before,
            day_template_id=test_day_template.id,
            is_override=False,
        )
        db.add(instance_day_before)
        await db.flush()

        slot_before = WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance_before.id,
            date=day_before,
            position=1,
            meal_type_id=test_meal_type.id,
            meal_id=test_meal.id,
            completion_status="followed",  # Completed
            completed_at=datetime.now(timezone.utc),
        )
        db.add(slot_before)
        await db.flush()

        response = await client.get("/api/v1/today")

        assert response.status_code == 200
        data = response.json()

        # Streak should be 0 because yesterday is incomplete
        assert data["stats"]["streak_days"] == 0
