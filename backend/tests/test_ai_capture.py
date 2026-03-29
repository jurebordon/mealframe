"""Tests for AI capture vision prompt and user meal context injection (ADR-013 Session 4)."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Meal, MealType, User
from app.services.ai_capture import build_vision_prompt, get_meal_context_for_prompt
from tests.conftest import ADMIN_USER_ID


# --- Pure unit tests for build_vision_prompt ---


class TestBuildVisionPrompt:
    """Tests for build_vision_prompt (no DB needed)."""

    def test_without_meal_context(self):
        """Prompt works without user meals (existing behavior)."""
        captured = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)
        prompt = build_vision_prompt(captured, meal_type_names=["Breakfast", "Lunch"])

        assert "Sunday, March 29 2026, 12:30" in prompt
        assert "Breakfast, Lunch" in prompt
        assert "user has these meals" not in prompt

    def test_with_meal_context(self):
        """Prompt includes user meal library when provided."""
        captured = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)
        user_meals = [
            {"name": "Chicken Stir-Fry", "portion": "200g chicken + 250g rice"},
            {"name": "Greek Yogurt Bowl", "portion": "200g yogurt + 30g granola"},
        ]
        prompt = build_vision_prompt(
            captured,
            meal_type_names=["Lunch"],
            user_meals=user_meals,
        )

        assert "user has these meals" in prompt
        assert "- Chicken Stir-Fry: 200g chicken + 250g rice" in prompt
        assert "- Greek Yogurt Bowl: 200g yogurt + 30g granola" in prompt
        assert "use their exact meal_name" in prompt

    def test_empty_meal_context_omitted(self):
        """Empty meal list does not inject context block."""
        captured = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)
        prompt = build_vision_prompt(captured, user_meals=[])

        assert "user has these meals" not in prompt

    def test_none_meal_context_omitted(self):
        """None meal list does not inject context block."""
        captured = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)
        prompt = build_vision_prompt(captured, user_meals=None)

        assert "user has these meals" not in prompt

    def test_default_meal_types_when_none_provided(self):
        """Falls back to default meal types when none provided."""
        captured = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)
        prompt = build_vision_prompt(captured)

        assert "breakfast, lunch, dinner, snack" in prompt

    def test_json_structure_preserved(self):
        """JSON output structure is present regardless of meal context."""
        captured = datetime(2026, 3, 29, 12, 30, tzinfo=timezone.utc)
        user_meals = [{"name": "Test Meal", "portion": "100g test"}]
        prompt = build_vision_prompt(captured, user_meals=user_meals)

        assert '"meal_name"' in prompt
        assert '"portion_description"' in prompt
        assert '"confidence_score"' in prompt


# --- Integration tests for get_meal_context_for_prompt ---


@pytest.mark.asyncio
class TestGetMealContextForPrompt:
    """Tests for get_meal_context_for_prompt (requires DB)."""

    async def test_returns_user_meals(self, db: AsyncSession, test_user: User, meal_type: MealType):
        """Returns meals with name and portion description."""
        meal = Meal(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Chicken Rice",
            portion_description="200g chicken + 150g rice",
            created_at=datetime.now(timezone.utc),
        )
        db.add(meal)
        await db.flush()

        result = await get_meal_context_for_prompt(db, test_user.id)

        names = [m["name"] for m in result]
        assert "Test Chicken Rice" in names
        matching = [m for m in result if m["name"] == "Test Chicken Rice"][0]
        assert matching["portion"] == "200g chicken + 150g rice"

    async def test_respects_limit(self, db: AsyncSession, test_user: User, meal_type: MealType):
        """Returns at most `limit` meals."""
        for i in range(5):
            db.add(Meal(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Limit Test Meal {i}",
                portion_description=f"Portion {i}",
                created_at=datetime(2026, 1, 1, 12, i, tzinfo=timezone.utc),
            ))
        await db.flush()

        result = await get_meal_context_for_prompt(db, test_user.id, limit=3)

        assert len(result) <= 3

    async def test_ordered_by_most_recent(self, db: AsyncSession, test_user: User, meal_type: MealType):
        """Most recently created meals come first."""
        old_meal = Meal(
            id=uuid4(),
            user_id=test_user.id,
            name="Old Meal",
            portion_description="old portion",
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        new_meal = Meal(
            id=uuid4(),
            user_id=test_user.id,
            name="New Meal",
            portion_description="new portion",
            created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        )
        db.add(old_meal)
        db.add(new_meal)
        await db.flush()

        result = await get_meal_context_for_prompt(db, test_user.id, limit=2)

        # New meal should come before old meal
        names = [m["name"] for m in result]
        if "New Meal" in names and "Old Meal" in names:
            assert names.index("New Meal") < names.index("Old Meal")

    async def test_scoped_to_user(self, db: AsyncSession, test_user: User):
        """Only returns meals belonging to the specified user."""
        other_user_id = uuid4()
        other_user = User(
            id=other_user_id,
            email=f"other-{uuid4().hex[:8]}@test.com",
            email_verified=True,
            is_active=True,
            auth_provider="email",
        )
        db.add(other_user)
        await db.flush()

        other_meal = Meal(
            id=uuid4(),
            user_id=other_user_id,
            name="Other User Meal",
            portion_description="should not appear",
            created_at=datetime.now(timezone.utc),
        )
        db.add(other_meal)
        await db.flush()

        result = await get_meal_context_for_prompt(db, test_user.id)

        names = [m["name"] for m in result]
        assert "Other User Meal" not in names

    async def test_empty_for_new_user(self, db: AsyncSession):
        """Returns empty list for user with no meals."""
        new_user_id = uuid4()
        new_user = User(
            id=new_user_id,
            email=f"new-{uuid4().hex[:8]}@test.com",
            email_verified=True,
            is_active=True,
            auth_provider="email",
        )
        db.add(new_user)
        await db.flush()

        result = await get_meal_context_for_prompt(db, new_user_id)

        assert result == []
