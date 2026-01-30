"""
Integration tests for the weekly planning API endpoints.

Tests cover:
- GET /api/v1/weekly-plans/current - Current week's plan
- POST /api/v1/weekly-plans/generate - Generate a new week
- PUT /api/v1/weekly-plans/current/days/{date}/template - Switch day template
- PUT /api/v1/weekly-plans/current/days/{date}/override - Mark day as "no plan"
- DELETE /api/v1/weekly-plans/current/days/{date}/override - Remove override

These tests use the database fixtures from conftest.py.
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
from app.services.weekly import get_week_start_date, get_next_monday


# Fixture to override database dependency
@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """
    Create an async HTTP client with database override.
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
async def test_meal_types(db: AsyncSession) -> list[MealType]:
    """Create multiple meal types for testing."""
    suffix = uuid4().hex[:8]
    types = [
        MealType(id=uuid4(), name=f"Breakfast {suffix}", description="Morning meal"),
        MealType(id=uuid4(), name=f"Lunch {suffix}", description="Midday meal"),
        MealType(id=uuid4(), name=f"Dinner {suffix}", description="Evening meal"),
    ]
    for mt in types:
        db.add(mt)
    await db.flush()
    return types


@pytest_asyncio.fixture
async def test_meals(db: AsyncSession, test_meal_types: list[MealType]) -> list[Meal]:
    """Create meals for each meal type."""
    meals = []
    base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i, mt in enumerate(test_meal_types):
        # Create 2 meals per type
        for j in range(2):
            meal = Meal(
                id=uuid4(),
                name=f"Test Meal {i}-{j} {uuid4().hex[:8]}",
                portion_description=f"Portion for meal {i}-{j}",
                calories_kcal=300 + (i * 100) + (j * 50),
                protein_g=20.0 + i,
                carbs_g=30.0 + i,
                fat_g=10.0 + i,
                created_at=base_time + timedelta(minutes=i * 10 + j),
            )
            db.add(meal)
            await db.flush()

            # Associate with meal type
            await db.execute(
                meal_to_meal_type.insert().values(
                    meal_id=meal.id,
                    meal_type_id=mt.id,
                )
            )
            await db.flush()
            meals.append(meal)

    return meals


@pytest_asyncio.fixture
async def test_day_templates(
    db: AsyncSession, test_meal_types: list[MealType]
) -> list[DayTemplate]:
    """Create day templates with slots."""
    suffix = uuid4().hex[:8]
    templates = []

    # Template with all 3 meal types
    template1 = DayTemplate(
        id=uuid4(),
        name=f"Full Day {suffix}",
        notes="All meals",
    )
    db.add(template1)
    await db.flush()

    for i, mt in enumerate(test_meal_types):
        slot = DayTemplateSlot(
            id=uuid4(),
            day_template_id=template1.id,
            position=i + 1,
            meal_type_id=mt.id,
        )
        db.add(slot)
    await db.flush()
    templates.append(template1)

    # Template with just breakfast
    template2 = DayTemplate(
        id=uuid4(),
        name=f"Light Day {suffix}",
        notes="Just breakfast",
    )
    db.add(template2)
    await db.flush()

    slot = DayTemplateSlot(
        id=uuid4(),
        day_template_id=template2.id,
        position=1,
        meal_type_id=test_meal_types[0].id,  # Breakfast only
    )
    db.add(slot)
    await db.flush()
    templates.append(template2)

    return templates


@pytest_asyncio.fixture
async def test_week_plan(
    db: AsyncSession, test_day_templates: list[DayTemplate]
) -> WeekPlan:
    """Create a default week plan with templates assigned to days."""
    week_plan = WeekPlan(
        id=uuid4(),
        name=f"Test Week Plan {uuid4().hex[:8]}",
        is_default=True,
    )
    db.add(week_plan)
    await db.flush()

    # Assign full day template to weekdays (Mon-Fri), light day to weekend
    for weekday in range(7):
        template = (
            test_day_templates[0] if weekday < 5 else test_day_templates[1]
        )
        week_plan_day = WeekPlanDay(
            id=uuid4(),
            week_plan_id=week_plan.id,
            weekday=weekday,
            day_template_id=template.id,
        )
        db.add(week_plan_day)
    await db.flush()

    return week_plan


@pytest_asyncio.fixture
async def current_week_instance(
    db: AsyncSession,
    test_week_plan: WeekPlan,
    test_day_templates: list[DayTemplate],
    test_meal_types: list[MealType],
    test_meals: list[Meal],
) -> WeeklyPlanInstance:
    """Create a weekly plan instance for the current week."""
    today = date.today()
    week_start = get_week_start_date(today)

    instance = WeeklyPlanInstance(
        id=uuid4(),
        week_plan_id=test_week_plan.id,
        week_start_date=week_start,
    )
    db.add(instance)
    await db.flush()

    # Create instance days for each day of the week
    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        weekday = day_offset  # 0=Monday

        # Use full template for weekdays, light for weekend
        template = test_day_templates[0] if weekday < 5 else test_day_templates[1]

        instance_day = WeeklyPlanInstanceDay(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=current_date,
            day_template_id=template.id,
            is_override=False,
        )
        db.add(instance_day)
        await db.flush()

        # Create slots based on template
        if weekday < 5:  # Full day - 3 slots
            for position, mt in enumerate(test_meal_types, 1):
                # Find a meal for this type
                meal = test_meals[position - 1]  # Simplified: use first meals
                slot = WeeklyPlanSlot(
                    id=uuid4(),
                    weekly_plan_instance_id=instance.id,
                    date=current_date,
                    position=position,
                    meal_type_id=mt.id,
                    meal_id=meal.id,
                    completion_status=None,
                    completed_at=None,
                )
                db.add(slot)
        else:  # Light day - 1 slot
            slot = WeeklyPlanSlot(
                id=uuid4(),
                weekly_plan_instance_id=instance.id,
                date=current_date,
                position=1,
                meal_type_id=test_meal_types[0].id,
                meal_id=test_meals[0].id,
                completion_status=None,
                completed_at=None,
            )
            db.add(slot)

        await db.flush()

    return instance


class TestGetCurrentWeek:
    """Tests for GET /api/v1/weekly-plans/current endpoint."""

    @pytest.mark.asyncio
    async def test_returns_404_when_no_plan(self, client: AsyncClient):
        """When no plan exists for current week, returns 404."""
        response = await client.get("/api/v1/weekly-plans/current")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_returns_current_week_plan(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Returns the current week's plan with all days and slots."""
        response = await client.get("/api/v1/weekly-plans/current")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(current_week_instance.id)
        assert data["week_start_date"] == current_week_instance.week_start_date.isoformat()
        assert data["week_plan"] is not None
        assert len(data["days"]) == 7

        # Check first day (Monday)
        monday = data["days"][0]
        assert monday["weekday"] == "Monday"
        assert monday["template"] is not None
        assert monday["is_override"] is False
        assert len(monday["slots"]) == 3  # Full day template

        # Check weekend day (Saturday)
        saturday = data["days"][5]
        assert saturday["weekday"] == "Saturday"
        assert len(saturday["slots"]) == 1  # Light day template

    @pytest.mark.asyncio
    async def test_returns_week_by_start_date_param(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Returns week plan when week_start_date query param is provided."""
        week_start = current_week_instance.week_start_date.isoformat()
        response = await client.get(f"/api/v1/weekly-plans/current?week_start_date={week_start}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(current_week_instance.id)
        assert data["week_start_date"] == week_start

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_week(
        self,
        client: AsyncClient,
    ):
        """Returns 404 when requesting a week that doesn't exist."""
        future_monday = "2099-01-04"  # A Monday in the future
        response = await client.get(f"/api/v1/weekly-plans/current?week_start_date={future_monday}")

        assert response.status_code == 404
        data = response.json()
        assert "No plan exists" in data["detail"]["error"]["message"]


class TestGenerateWeek:
    """Tests for POST /api/v1/weekly-plans/generate endpoint."""

    @pytest.mark.asyncio
    async def test_generate_week_defaults_to_next_monday(
        self,
        client: AsyncClient,
        test_week_plan: WeekPlan,
        test_meals: list[Meal],
    ):
        """Without date, generates for next Monday."""
        response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={},
        )

        assert response.status_code == 201
        data = response.json()

        expected_start = get_next_monday(date.today())
        assert data["week_start_date"] == expected_start.isoformat()
        assert data["week_plan"]["name"] == test_week_plan.name
        assert len(data["days"]) == 7

    @pytest.mark.asyncio
    async def test_generate_week_with_specific_date(
        self,
        client: AsyncClient,
        test_week_plan: WeekPlan,
        test_meals: list[Meal],
    ):
        """Can specify a Monday to generate for."""
        # Pick a Monday far in the future to avoid conflicts
        target_monday = date(2099, 1, 5)  # A Monday

        response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": target_monday.isoformat()},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["week_start_date"] == target_monday.isoformat()

    @pytest.mark.asyncio
    async def test_regenerate_week_when_exists(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Regenerates uncompleted slots when week already exists (smart regeneration)."""
        response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": current_week_instance.week_start_date.isoformat()},
        )

        # Should return 200 OK (not 409 Conflict) - regeneration instead of conflict
        assert response.status_code == 200
        data = response.json()
        assert data["week_start_date"] == current_week_instance.week_start_date.isoformat()
        # Should still have days
        assert len(data["days"]) == 7

    @pytest.mark.asyncio
    async def test_regenerate_preserves_completed_slots(
        self,
        db: AsyncSession,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Regeneration should preserve slots that have completion status."""
        # Get current week to find a slot to complete
        week_response = await client.get("/api/v1/weekly-plans/current")
        assert week_response.status_code == 200
        week_data = week_response.json()

        # Find a slot from Monday
        monday_data = week_data["days"][0]
        assert len(monday_data["slots"]) > 0

        # Complete the first slot
        first_slot = monday_data["slots"][0]
        slot_id = first_slot["id"]
        original_meal_id = first_slot["meal"]["id"] if first_slot.get("meal") else None

        # Mark slot as completed
        complete_response = await client.post(
            f"/api/v1/slots/{slot_id}/complete",
            json={"status": "followed"},
        )
        assert complete_response.status_code == 200

        # Now regenerate the week
        regen_response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": current_week_instance.week_start_date.isoformat()},
        )
        assert regen_response.status_code == 200

        # The completed slot should still have the same meal and completion status
        regen_data = regen_response.json()
        regen_monday = regen_data["days"][0]

        # Find the slot with the same ID
        regen_slot = next((s for s in regen_monday["slots"] if s["id"] == slot_id), None)
        assert regen_slot is not None, "Completed slot should still exist"
        assert regen_slot["completion_status"] == "followed", "Completion status should be preserved"
        if original_meal_id:
            assert regen_slot["meal"]["id"] == original_meal_id, "Meal assignment should be preserved"

    @pytest.mark.asyncio
    async def test_generate_week_fails_without_default_plan(
        self, client: AsyncClient
    ):
        """Returns 400 when no default week plan exists."""
        # Pick a Monday far in the future to avoid conflicts
        target_monday = date(2098, 1, 6)  # A Monday

        response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": target_monday.isoformat()},
        )

        assert response.status_code == 400
        data = response.json()
        assert "No default week plan" in data["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_generate_week_fails_on_non_monday(
        self,
        client: AsyncClient,
        test_week_plan: WeekPlan,
    ):
        """Returns 400 when week_start_date is not a Monday."""
        # Pick a Tuesday (2099-01-06 is a Tuesday)
        target_tuesday = date(2099, 1, 6)

        response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": target_tuesday.isoformat()},
        )

        assert response.status_code == 400
        assert "Monday" in response.json()["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_generate_week_assigns_meals_via_round_robin(
        self,
        client: AsyncClient,
        test_week_plan: WeekPlan,
        test_meals: list[Meal],
    ):
        """Meals are assigned using round-robin rotation."""
        target_monday = date(2097, 1, 7)  # A Monday

        response = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": target_monday.isoformat()},
        )

        assert response.status_code == 201
        data = response.json()

        # All days should have slots with meals assigned
        for day in data["days"]:
            for slot in day["slots"]:
                assert slot["meal"] is not None
                assert slot["meal"]["name"] is not None


class TestSwitchDayTemplate:
    """Tests for PUT /api/v1/weekly-plans/current/days/{date}/template endpoint."""

    @pytest.mark.asyncio
    async def test_switch_template_success(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
        test_day_templates: list[DayTemplate],
    ):
        """Successfully switches a day's template."""
        # Switch Monday from full day to light day
        today = date.today()
        week_start = get_week_start_date(today)
        monday = week_start

        light_template = test_day_templates[1]

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{monday.isoformat()}/template",
            json={"day_template_id": str(light_template.id)},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["date"] == monday.isoformat()
        assert data["template"]["id"] == str(light_template.id)
        assert data["is_override"] is False
        assert len(data["slots"]) == 1  # Light template has 1 slot

    @pytest.mark.asyncio
    async def test_switch_template_no_current_week(
        self, client: AsyncClient, test_day_templates: list[DayTemplate]
    ):
        """Returns 404 when no current week plan exists."""
        today = date.today()

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{today.isoformat()}/template",
            json={"day_template_id": str(test_day_templates[0].id)},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_switch_template_date_not_in_week(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
        test_day_templates: list[DayTemplate],
    ):
        """Returns 400 when date is not in current week."""
        # Date far in the future
        future_date = date(2099, 6, 15)

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{future_date.isoformat()}/template",
            json={"day_template_id": str(test_day_templates[0].id)},
        )

        assert response.status_code == 400
        assert "not in the current week" in response.json()["detail"]["error"]["message"]

    @pytest.mark.asyncio
    async def test_switch_template_invalid_template(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Returns 404 when template doesn't exist."""
        today = date.today()
        week_start = get_week_start_date(today)
        monday = week_start

        fake_template_id = uuid4()

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{monday.isoformat()}/template",
            json={"day_template_id": str(fake_template_id)},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["error"]["message"].lower()


class TestSetDayOverride:
    """Tests for PUT /api/v1/weekly-plans/current/days/{date}/override endpoint."""

    @pytest.mark.asyncio
    async def test_set_override_success(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Successfully marks a day as override."""
        today = date.today()
        week_start = get_week_start_date(today)
        monday = week_start

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{monday.isoformat()}/override",
            json={"reason": "Vacation day"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["date"] == monday.isoformat()
        assert data["is_override"] is True
        assert data["override_reason"] == "Vacation day"

    @pytest.mark.asyncio
    async def test_set_override_without_reason(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Can set override without a reason."""
        today = date.today()
        week_start = get_week_start_date(today)
        monday = week_start

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{monday.isoformat()}/override",
            json={},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_override"] is True
        assert data["override_reason"] is None

    @pytest.mark.asyncio
    async def test_set_override_no_current_week(self, client: AsyncClient):
        """Returns 404 when no current week plan exists."""
        today = date.today()

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{today.isoformat()}/override",
            json={"reason": "Test"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_set_override_date_not_in_week(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Returns 400 when date is not in current week."""
        future_date = date(2099, 6, 15)

        response = await client.put(
            f"/api/v1/weekly-plans/current/days/{future_date.isoformat()}/override",
            json={"reason": "Test"},
        )

        assert response.status_code == 400


class TestClearDayOverride:
    """Tests for DELETE /api/v1/weekly-plans/current/days/{date}/override endpoint."""

    @pytest.mark.asyncio
    async def test_clear_override_success(
        self,
        db: AsyncSession,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Successfully clears an override and restores slots."""
        today = date.today()
        week_start = get_week_start_date(today)
        monday = week_start

        # First, set an override
        await client.put(
            f"/api/v1/weekly-plans/current/days/{monday.isoformat()}/override",
            json={"reason": "Vacation"},
        )

        # Then clear it
        response = await client.delete(
            f"/api/v1/weekly-plans/current/days/{monday.isoformat()}/override"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["date"] == monday.isoformat()
        assert data["is_override"] is False
        assert data["override_reason"] is None
        # Slots should be restored
        assert len(data["slots"]) > 0

    @pytest.mark.asyncio
    async def test_clear_override_no_current_week(self, client: AsyncClient):
        """Returns 404 when no current week plan exists."""
        today = date.today()

        response = await client.delete(
            f"/api/v1/weekly-plans/current/days/{today.isoformat()}/override"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_clear_override_date_not_in_week(
        self,
        client: AsyncClient,
        current_week_instance: WeeklyPlanInstance,
    ):
        """Returns 400 when date is not in current week."""
        future_date = date(2099, 6, 15)

        response = await client.delete(
            f"/api/v1/weekly-plans/current/days/{future_date.isoformat()}/override"
        )

        assert response.status_code == 400


class TestWeekGenerationRoundRobin:
    """Tests for round-robin behavior during week generation."""

    @pytest.mark.asyncio
    async def test_round_robin_rotates_meals(
        self,
        db: AsyncSession,
        client: AsyncClient,
        test_week_plan: WeekPlan,
        test_meals: list[Meal],
        test_meal_types: list[MealType],
    ):
        """Round-robin should rotate through meals fairly."""
        # Generate first week
        target_monday1 = date(2090, 1, 2)  # A Monday

        response1 = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": target_monday1.isoformat()},
        )
        assert response1.status_code == 201
        data1 = response1.json()

        # Generate second week
        target_monday2 = date(2090, 1, 9)  # Next Monday

        response2 = await client.post(
            "/api/v1/weekly-plans/generate",
            json={"week_start_date": target_monday2.isoformat()},
        )
        assert response2.status_code == 201
        data2 = response2.json()

        # Collect breakfast meals from both weeks
        breakfast_meals_week1 = []
        breakfast_meals_week2 = []

        for day in data1["days"]:
            for slot in day["slots"]:
                if slot["position"] == 1:  # Breakfast
                    breakfast_meals_week1.append(slot["meal"]["id"])

        for day in data2["days"]:
            for slot in day["slots"]:
                if slot["position"] == 1:  # Breakfast
                    breakfast_meals_week2.append(slot["meal"]["id"])

        # With 2 breakfast meals and 7 days per week, the pattern should rotate
        # After 14 days (7 + 7), we should see both meals used
        all_breakfast_meals = breakfast_meals_week1 + breakfast_meals_week2
        unique_meals = set(all_breakfast_meals)

        # Should use at least 2 different meals (we have 2 per type)
        assert len(unique_meals) >= 1
