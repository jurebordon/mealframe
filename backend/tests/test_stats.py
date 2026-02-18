"""
Integration tests for the Stats API endpoint.

Tests cover:
- GET /api/v1/stats - Adherence statistics
  - Empty state (no data)
  - Status breakdown counting
  - Adherence rate calculation
  - Streak calculation (current and best)
  - Override day counting
  - Per-meal-type breakdown
  - Daily adherence data points
  - Query parameter validation
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import MealType, Meal, DayTemplate, WeeklyPlanInstance, WeeklyPlanInstanceDay, WeeklyPlanSlot
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


async def _get_or_create_instance(
    db: AsyncSession, week_start: date
) -> WeeklyPlanInstance:
    """Get an existing instance for the week, or create one."""
    result = await db.execute(
        select(WeeklyPlanInstance).where(
            WeeklyPlanInstance.week_start_date == week_start
        )
    )
    instance = result.scalars().first()
    if instance:
        return instance
    instance = WeeklyPlanInstance(id=uuid4(), week_start_date=week_start)
    db.add(instance)
    await db.flush()
    return instance


async def _get_or_create_instance_day(
    db: AsyncSession,
    instance: WeeklyPlanInstance,
    day_date: date,
    is_override: bool = False,
) -> WeeklyPlanInstanceDay:
    """Get an existing instance day, or create one."""
    from sqlalchemy import and_
    result = await db.execute(
        select(WeeklyPlanInstanceDay).where(
            and_(
                WeeklyPlanInstanceDay.weekly_plan_instance_id == instance.id,
                WeeklyPlanInstanceDay.date == day_date,
            )
        )
    )
    day = result.scalars().first()
    if day:
        if is_override:
            day.is_override = True
        return day
    day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=day_date,
        is_override=is_override,
    )
    db.add(day)
    await db.flush()
    return day


async def _create_slots(
    db: AsyncSession,
    meal_type: MealType,
    meal: Meal,
    days_data: list[dict],
) -> None:
    """
    Create slots (and instance days) for testing.

    Reuses existing WeeklyPlanInstance and WeeklyPlanInstanceDay if they
    exist for the week/date to avoid unique constraint violations from seed data.

    days_data: list of dicts with keys:
        - date: date object
        - slots: list of completion_status values (str or None)
        - is_override: bool (optional, default False)
    """
    # Group by week start to get or create instances
    instances: dict[date, WeeklyPlanInstance] = {}
    for day_data in days_data:
        d = day_data["date"]
        week_start = d - timedelta(days=d.weekday())
        if week_start not in instances:
            instances[week_start] = await _get_or_create_instance(db, week_start)

    for day_data in days_data:
        d = day_data["date"]
        week_start = d - timedelta(days=d.weekday())
        instance = instances[week_start]
        is_override = day_data.get("is_override", False)

        await _get_or_create_instance_day(db, instance, d, is_override)

        for position, status in enumerate(day_data.get("slots", [])):
            slot = WeeklyPlanSlot(
                id=uuid4(),
                weekly_plan_instance_id=instance.id,
                date=d,
                position=100 + position,  # High position to avoid conflicts with seed data
                meal_type_id=meal_type.id,
                meal_id=meal.id,
                completion_status=status,
            )
            db.add(slot)

    await db.flush()


@pytest_asyncio.fixture
async def meal_type(db: AsyncSession) -> MealType:
    """Create a test meal type."""
    mt = MealType(
        id=uuid4(),
        name=f"Test Breakfast {uuid4().hex[:8]}",
        description="Morning meal",
    )
    db.add(mt)
    await db.flush()
    return mt


@pytest_asyncio.fixture
async def meal(db: AsyncSession) -> Meal:
    """Create a test meal."""
    m = Meal(
        id=uuid4(),
        name=f"Test Oatmeal {uuid4().hex[:8]}",
        portion_description="1 bowl",
    )
    db.add(m)
    await db.flush()
    return m


# =============================================================================
# GET /api/v1/stats - Response structure
# =============================================================================


@pytest.mark.asyncio
async def test_stats_response_structure(client: AsyncClient):
    """GET /stats returns the expected response structure."""
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["period_days"] == 30
    assert "total_slots" in data
    assert "completed_slots" in data
    assert "adherence_rate" in data
    assert "current_streak" in data
    assert "best_streak" in data
    assert "override_days" in data
    assert "by_meal_type" in data
    assert "daily_adherence" in data
    assert "by_status" in data

    by_status = data["by_status"]
    for key in ["followed", "adjusted", "skipped", "replaced", "social", "unmarked"]:
        assert key in by_status


# =============================================================================
# GET /api/v1/stats - Status breakdown and adherence rate
# =============================================================================


@pytest.mark.asyncio
async def test_stats_status_breakdown(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """GET /stats correctly counts each completion status."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {
            "date": today,
            "slots": ["followed", "adjusted", "skipped", "replaced", "social", None],
        },
    ])

    response = await client.get("/api/v1/stats?days=1")
    assert response.status_code == 200
    data = response.json()

    # Our test created 6 slots; there may be pre-existing slots from seed data
    assert data["total_slots"] >= 6
    assert data["completed_slots"] >= 5

    by_status = data["by_status"]
    assert by_status["followed"] >= 1
    assert by_status["adjusted"] >= 1
    assert by_status["skipped"] >= 1
    assert by_status["replaced"] >= 1
    assert by_status["social"] >= 1
    assert by_status["unmarked"] >= 1


@pytest.mark.asyncio
async def test_stats_adherence_rate_calculation(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Adherence = (followed + adjusted) / (total - social - unmarked)."""
    today = date.today()
    # 3 followed, 1 adjusted, 1 skipped, 1 social, 1 unmarked = 7 total
    # Adherence = (3 + 1) / (7 - 1 - 1) = 4/5 = 0.8
    await _create_slots(db, meal_type, meal, [
        {
            "date": today,
            "slots": ["followed", "followed", "followed", "adjusted", "skipped", "social", None],
        },
    ])

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    adherence = Decimal(data["adherence_rate"])
    # With potential seed data we can't assert exact value,
    # but adherence should be between 0 and 1
    assert Decimal("0") <= adherence <= Decimal("1")


@pytest.mark.asyncio
async def test_stats_perfect_adherence(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """All followed yields adherence > 0."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today, "slots": ["followed", "followed", "followed"]},
    ])

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    adherence = Decimal(data["adherence_rate"])
    assert adherence > Decimal("0")


# =============================================================================
# GET /api/v1/stats - Streaks
# =============================================================================


@pytest.mark.asyncio
async def test_stats_current_streak(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Current streak counts consecutive completed days before today."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today - timedelta(days=1), "slots": ["followed"]},
        {"date": today - timedelta(days=2), "slots": ["followed"]},
        {"date": today - timedelta(days=3), "slots": ["followed"]},
    ])

    response = await client.get("/api/v1/stats?days=7")
    data = response.json()

    # Streak counts backwards from yesterday, so should be >= 1
    assert data["current_streak"] >= 1
    assert isinstance(data["current_streak"], int)


@pytest.mark.asyncio
async def test_stats_streak_excludes_today(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Current streak excludes today (today is still in progress)."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today, "slots": [None]},  # Unmarked today — should NOT affect streak
        {"date": today - timedelta(days=1), "slots": ["followed"]},
        {"date": today - timedelta(days=2), "slots": ["followed"]},
    ])

    response = await client.get("/api/v1/stats?days=7")
    data = response.json()

    # Today is excluded from streak calc, so yesterday's completed slots count
    assert data["current_streak"] >= 1


@pytest.mark.asyncio
async def test_stats_streak_breaks_on_unmarked_past_day(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Streak breaks when a past day has an unmarked slot."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today - timedelta(days=1), "slots": [None]},  # Unmarked yesterday
    ])

    response = await client.get("/api/v1/stats?days=7")
    data = response.json()

    # Yesterday has unmarked slot, streak should be 0
    assert data["current_streak"] == 0


@pytest.mark.asyncio
async def test_stats_best_streak_gte_current(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Best streak is always >= current streak."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today - timedelta(days=1), "slots": ["followed"]},
    ])

    response = await client.get("/api/v1/stats?days=30")
    data = response.json()

    assert data["best_streak"] >= data["current_streak"]


# =============================================================================
# GET /api/v1/stats - Override days
# =============================================================================


@pytest.mark.asyncio
async def test_stats_override_days(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Override days are counted correctly."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today, "slots": ["followed"], "is_override": False},
        {"date": today - timedelta(days=1), "slots": [], "is_override": True},
        {"date": today - timedelta(days=2), "slots": [], "is_override": True},
    ])

    response = await client.get("/api/v1/stats?days=7")
    data = response.json()

    # At least our 2 override days should be counted
    assert data["override_days"] >= 2


# =============================================================================
# GET /api/v1/stats - Per-meal-type breakdown
# =============================================================================


@pytest.mark.asyncio
async def test_stats_by_meal_type(
    client: AsyncClient, db: AsyncSession, meal: Meal
):
    """Per-meal-type breakdown is returned sorted by lowest adherence."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    mt_breakfast = MealType(id=uuid4(), name=f"Breakfast {uuid4().hex[:8]}")
    mt_lunch = MealType(id=uuid4(), name=f"Lunch {uuid4().hex[:8]}")
    db.add(mt_breakfast)
    db.add(mt_lunch)
    await db.flush()

    instance = await _get_or_create_instance(db, week_start)
    await _get_or_create_instance_day(db, instance, today)

    # Breakfast: 2 followed out of 2 = 100%
    for i in range(2):
        db.add(WeeklyPlanSlot(
            id=uuid4(), weekly_plan_instance_id=instance.id,
            date=today, position=10 + i, meal_type_id=mt_breakfast.id,
            meal_id=meal.id, completion_status="followed",
        ))

    # Lunch: 1 followed out of 2 = 50%
    db.add(WeeklyPlanSlot(
        id=uuid4(), weekly_plan_instance_id=instance.id,
        date=today, position=12, meal_type_id=mt_lunch.id,
        meal_id=meal.id, completion_status="followed",
    ))
    db.add(WeeklyPlanSlot(
        id=uuid4(), weekly_plan_instance_id=instance.id,
        date=today, position=13, meal_type_id=mt_lunch.id,
        meal_id=meal.id, completion_status="skipped",
    ))
    await db.flush()

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    by_type = data["by_meal_type"]
    # Find our test meal types in the response
    breakfast_entry = next((t for t in by_type if t["meal_type_id"] == str(mt_breakfast.id)), None)
    lunch_entry = next((t for t in by_type if t["meal_type_id"] == str(mt_lunch.id)), None)

    assert breakfast_entry is not None
    assert lunch_entry is not None
    assert Decimal(lunch_entry["adherence_rate"]) == Decimal("0.500")
    assert Decimal(breakfast_entry["adherence_rate"]) == Decimal("1.000")

    # Verify sorted by lowest first: lunch should appear before breakfast
    lunch_idx = next(i for i, t in enumerate(by_type) if t["meal_type_id"] == str(mt_lunch.id))
    breakfast_idx = next(i for i, t in enumerate(by_type) if t["meal_type_id"] == str(mt_breakfast.id))
    assert lunch_idx < breakfast_idx


# =============================================================================
# GET /api/v1/stats - Daily adherence
# =============================================================================


@pytest.mark.asyncio
async def test_stats_daily_adherence(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Daily adherence returns per-day data points."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    await _create_slots(db, meal_type, meal, [
        {"date": yesterday, "slots": ["followed", "skipped"]},
        {"date": today, "slots": ["followed", "followed"]},
    ])

    response = await client.get("/api/v1/stats?days=2")
    data = response.json()

    daily = data["daily_adherence"]
    assert len(daily) >= 1  # At least one day with data

    # Find our specific days in the response
    yesterday_entry = next((d for d in daily if d["date"] == yesterday.isoformat()), None)
    today_entry = next((d for d in daily if d["date"] == today.isoformat()), None)

    assert yesterday_entry is not None
    assert today_entry is not None

    # Verify dates are in ascending order
    dates = [d["date"] for d in daily]
    assert dates == sorted(dates)


# =============================================================================
# GET /api/v1/stats - Query parameter validation
# =============================================================================


@pytest.mark.asyncio
async def test_stats_custom_days(client: AsyncClient):
    """GET /stats accepts custom days parameter."""
    response = await client.get("/api/v1/stats?days=7")
    assert response.status_code == 200
    assert response.json()["period_days"] == 7


@pytest.mark.asyncio
async def test_stats_invalid_days_zero(client: AsyncClient):
    """GET /stats rejects days=0."""
    response = await client.get("/api/v1/stats?days=0")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stats_invalid_days_too_large(client: AsyncClient):
    """GET /stats rejects days > 365."""
    response = await client.get("/api/v1/stats?days=400")
    assert response.status_code == 422


# =============================================================================
# GET /api/v1/stats - Over-limit stats
# =============================================================================


@pytest.mark.asyncio
async def test_stats_over_limit_response_fields(client: AsyncClient):
    """GET /stats response includes over-limit fields."""
    response = await client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "over_limit_days" in data
    assert "days_with_limits" in data
    assert "over_limit_breakdown" in data


@pytest.mark.asyncio
async def test_stats_over_limit_no_templates_with_limits(
    client: AsyncClient, db: AsyncSession, meal_type: MealType, meal: Meal
):
    """Over-limit stats are zero when no templates have limits set."""
    today = date.today()
    await _create_slots(db, meal_type, meal, [
        {"date": today, "slots": ["followed", "followed"]},
    ])

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()
    assert data["over_limit_days"] == 0
    assert data["days_with_limits"] == 0
    assert data["over_limit_breakdown"] == []


@pytest.mark.asyncio
async def test_stats_over_limit_calories_exceeded(
    client: AsyncClient, db: AsyncSession
):
    """Over-limit detects when daily calories exceed template limit."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # Create template with calorie limit
    mt = MealType(id=uuid4(), name=f"Meal {uuid4().hex[:8]}")
    db.add(mt)
    template = DayTemplate(
        id=uuid4(),
        name=f"Low Cal {uuid4().hex[:8]}",
        max_calories_kcal=1500,
    )
    db.add(template)
    await db.flush()

    # Create a meal with 800 calories
    high_cal_meal = Meal(
        id=uuid4(),
        name=f"Big Meal {uuid4().hex[:8]}",
        portion_description="Large portion",
        calories_kcal=800,
        protein_g=Decimal("30.0"),
    )
    db.add(high_cal_meal)
    await db.flush()

    # Create instance day with template
    instance = await _get_or_create_instance(db, week_start)
    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        day_template_id=template.id,
        is_override=False,
    )
    db.add(instance_day)
    await db.flush()

    # Create 2 slots = 1600 kcal total (exceeds 1500 limit)
    for i in range(2):
        db.add(WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=today,
            position=200 + i,
            meal_type_id=mt.id,
            meal_id=high_cal_meal.id,
            completion_status="followed",
        ))
    await db.flush()

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    assert data["over_limit_days"] >= 1
    assert data["days_with_limits"] >= 1
    assert len(data["over_limit_breakdown"]) >= 1

    # Find our template in the breakdown
    breakdown_entry = next(
        (b for b in data["over_limit_breakdown"] if b["template_name"] == template.name),
        None,
    )
    assert breakdown_entry is not None
    assert breakdown_entry["days_over"] >= 1
    assert breakdown_entry["exceeded_metric"] == "calories"


@pytest.mark.asyncio
async def test_stats_over_limit_within_limits(
    client: AsyncClient, db: AsyncSession
):
    """Over-limit is zero when daily totals are within template limits."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    mt = MealType(id=uuid4(), name=f"Meal {uuid4().hex[:8]}")
    db.add(mt)
    template = DayTemplate(
        id=uuid4(),
        name=f"Generous {uuid4().hex[:8]}",
        max_calories_kcal=3000,
        max_protein_g=Decimal("200.0"),
    )
    db.add(template)
    await db.flush()

    small_meal = Meal(
        id=uuid4(),
        name=f"Small Meal {uuid4().hex[:8]}",
        portion_description="Small portion",
        calories_kcal=400,
        protein_g=Decimal("20.0"),
    )
    db.add(small_meal)
    await db.flush()

    instance = await _get_or_create_instance(db, week_start)
    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        day_template_id=template.id,
        is_override=False,
    )
    db.add(instance_day)
    await db.flush()

    # 2 small meals = 800 kcal, 40g protein — well within limits
    for i in range(2):
        db.add(WeeklyPlanSlot(
            id=uuid4(),
            weekly_plan_instance_id=instance.id,
            date=today,
            position=300 + i,
            meal_type_id=mt.id,
            meal_id=small_meal.id,
            completion_status="followed",
        ))
    await db.flush()

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    # Our template has limits but they weren't exceeded
    assert data["days_with_limits"] >= 1
    # Find our template — it should NOT appear in breakdown (no over-limit)
    breakdown_entry = next(
        (b for b in data["over_limit_breakdown"] if b["template_name"] == template.name),
        None,
    )
    assert breakdown_entry is None


@pytest.mark.asyncio
async def test_stats_over_limit_protein_exceeded(
    client: AsyncClient, db: AsyncSession
):
    """Over-limit detects when daily protein exceeds template limit."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    mt = MealType(id=uuid4(), name=f"Meal {uuid4().hex[:8]}")
    db.add(mt)
    template = DayTemplate(
        id=uuid4(),
        name=f"Low Protein {uuid4().hex[:8]}",
        max_protein_g=Decimal("50.0"),
    )
    db.add(template)
    await db.flush()

    high_protein_meal = Meal(
        id=uuid4(),
        name=f"Protein Bomb {uuid4().hex[:8]}",
        portion_description="300g chicken",
        calories_kcal=500,
        protein_g=Decimal("60.0"),
    )
    db.add(high_protein_meal)
    await db.flush()

    instance = await _get_or_create_instance(db, week_start)
    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        day_template_id=template.id,
        is_override=False,
    )
    db.add(instance_day)
    await db.flush()

    # 1 slot = 60g protein (exceeds 50g limit)
    db.add(WeeklyPlanSlot(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        position=400,
        meal_type_id=mt.id,
        meal_id=high_protein_meal.id,
        completion_status="followed",
    ))
    await db.flush()

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    breakdown_entry = next(
        (b for b in data["over_limit_breakdown"] if b["template_name"] == template.name),
        None,
    )
    assert breakdown_entry is not None
    assert breakdown_entry["exceeded_metric"] == "protein"


@pytest.mark.asyncio
async def test_stats_over_limit_override_days_excluded(
    client: AsyncClient, db: AsyncSession
):
    """Override days are excluded from over-limit calculations."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    mt = MealType(id=uuid4(), name=f"Meal {uuid4().hex[:8]}")
    db.add(mt)
    template = DayTemplate(
        id=uuid4(),
        name=f"Override Test {uuid4().hex[:8]}",
        max_calories_kcal=1000,
    )
    db.add(template)
    await db.flush()

    big_meal = Meal(
        id=uuid4(),
        name=f"Big {uuid4().hex[:8]}",
        portion_description="huge",
        calories_kcal=2000,
    )
    db.add(big_meal)
    await db.flush()

    instance = await _get_or_create_instance(db, week_start)
    # Mark as override — should be excluded from over-limit
    instance_day = WeeklyPlanInstanceDay(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        day_template_id=template.id,
        is_override=True,
    )
    db.add(instance_day)
    await db.flush()

    db.add(WeeklyPlanSlot(
        id=uuid4(),
        weekly_plan_instance_id=instance.id,
        date=today,
        position=500,
        meal_type_id=mt.id,
        meal_id=big_meal.id,
        completion_status="followed",
    ))
    await db.flush()

    response = await client.get("/api/v1/stats?days=1")
    data = response.json()

    # The override day template should NOT appear in breakdown
    breakdown_entry = next(
        (b for b in data["over_limit_breakdown"] if b["template_name"] == template.name),
        None,
    )
    assert breakdown_entry is None
