"""
Pytest configuration and fixtures for MealFrame tests.

This module provides:
- Async test configuration
- Database session fixtures for testing
- Common test fixtures for meals and meal types

Note: We use PostgreSQL for tests because the models use PostgreSQL-specific
features like ARRAY types. Tests require Docker to be running with the
database container available.
"""
import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Meal, MealType, RoundRobinState, User
from app.models.meal_to_meal_type import meal_to_meal_type


# Use test PostgreSQL database (same as dev but isolated via transactions)
# Default to local docker-compose database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://mealframe:password@localhost:5436/mealframe"
)

# Must match the admin user ID from the migration
ADMIN_USER_ID = UUID("00000000-0000-4000-a000-000000000001")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    Create a test database engine.

    Uses session scope to reuse engine across all tests for performance.
    Tables are created once at the start of the test session.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables (idempotent - won't fail if they exist)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with automatic rollback.

    Each test gets a fresh session that rolls back all changes at the end,
    ensuring test isolation without the overhead of recreating tables.
    """
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session() as session:
        # Start a savepoint so we can rollback to clean state
        await session.begin_nested()

        yield session

        # Rollback all changes made during the test
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """
    Get or create a test user for all fixtures.

    Uses the admin user seeded by migration (deterministic UUID).
    Falls back to creating one if it doesn't exist (e.g., fresh test DB).
    """
    result = await db.execute(select(User).where(User.id == ADMIN_USER_ID))
    user = result.scalars().first()
    if user:
        return user

    user = User(
        id=ADMIN_USER_ID,
        email="admin@mealframe.io",
        email_verified=True,
        is_active=True,
        auth_provider="email",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def meal_type(db: AsyncSession, test_user: User) -> MealType:
    """Create a single meal type for testing."""
    mt = MealType(
        id=uuid4(),
        user_id=test_user.id,
        name=f"Test Breakfast {uuid4().hex[:8]}",  # Unique name for isolation
        description="Test meal type",
    )
    db.add(mt)
    await db.flush()
    return mt


@pytest_asyncio.fixture
async def meal_types(db: AsyncSession, test_user: User) -> list[MealType]:
    """Create multiple meal types for testing."""
    suffix = uuid4().hex[:8]  # Unique suffix for isolation
    types = [
        MealType(id=uuid4(), user_id=test_user.id, name=f"Breakfast {suffix}", description="Morning meal"),
        MealType(id=uuid4(), user_id=test_user.id, name=f"Lunch {suffix}", description="Midday meal"),
        MealType(id=uuid4(), user_id=test_user.id, name=f"Dinner {suffix}", description="Evening meal"),
    ]
    for mt in types:
        db.add(mt)
    await db.flush()
    return types


async def create_meal(
    db: AsyncSession,
    name: str,
    meal_type: MealType,
    created_at: datetime | None = None,
    user_id: UUID | None = None,
) -> Meal:
    """Helper to create a meal with a specific creation time."""
    meal = Meal(
        id=uuid4(),
        user_id=user_id or meal_type.user_id,
        name=name,
        portion_description=f"Test portion for {name}",
        created_at=created_at or datetime.now(timezone.utc),
    )
    db.add(meal)
    await db.flush()

    # Add meal to meal type
    await db.execute(
        meal_to_meal_type.insert().values(
            meal_id=meal.id,
            meal_type_id=meal_type.id,
        )
    )
    await db.flush()

    return meal


async def create_meals_with_timestamps(
    db: AsyncSession,
    meal_type: MealType,
    count: int,
    base_time: datetime | None = None,
) -> list[Meal]:
    """
    Create multiple meals with sequential timestamps.

    Each meal is created with a timestamp 1 minute after the previous one,
    ensuring deterministic ordering.
    """
    base = base_time or datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    meals = []

    for i in range(count):
        meal = await create_meal(
            db,
            name=f"Meal {i + 1}",
            meal_type=meal_type,
            created_at=base + timedelta(minutes=i),
        )
        meals.append(meal)

    return meals
