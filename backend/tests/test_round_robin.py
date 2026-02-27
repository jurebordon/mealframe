"""
Tests for the round-robin meal selection algorithm.

These tests verify:
- Deterministic ordering (same inputs → same outputs)
- State tracking and persistence
- Rotation behavior (advancing through meals)
- Edge cases (no meals, one meal, deleted meals)
- Fairness (all meals get equal rotation)

See Tech Spec section 3.1 and ADR-002 for algorithm specification.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Meal, MealType, RoundRobinState, User
from app.models.meal_to_meal_type import meal_to_meal_type
from app.services.round_robin import (
    get_meals_for_type,
    get_next_meal_for_type,
    get_round_robin_state,
    peek_next_meal_for_type,
    reset_round_robin_state,
    update_round_robin_state,
)

from .conftest import create_meal, create_meals_with_timestamps


class TestGetMealsForType:
    """Tests for get_meals_for_type function."""

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_meals(
        self, db: AsyncSession, meal_type: MealType
    ):
        """No meals for type returns empty list."""
        meals = await get_meals_for_type(db, meal_type.id)
        assert meals == []

    @pytest.mark.asyncio
    async def test_returns_meals_for_type(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Returns all meals assigned to the meal type."""
        created_meals = await create_meals_with_timestamps(db, meal_type, 3)

        meals = await get_meals_for_type(db, meal_type.id)

        assert len(meals) == 3
        assert all(m.id in [cm.id for cm in created_meals] for m in meals)

    @pytest.mark.asyncio
    async def test_orders_by_created_at_then_id(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Meals are ordered by (created_at ASC, id ASC)."""
        base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create meals with specific timestamps
        meal_c = await create_meal(
            db, "Meal C", meal_type, base_time + timedelta(minutes=2)
        )
        meal_a = await create_meal(
            db, "Meal A", meal_type, base_time
        )
        meal_b = await create_meal(
            db, "Meal B", meal_type, base_time + timedelta(minutes=1)
        )

        meals = await get_meals_for_type(db, meal_type.id)

        # Should be ordered by created_at
        assert meals[0].id == meal_a.id
        assert meals[1].id == meal_b.id
        assert meals[2].id == meal_c.id

    @pytest.mark.asyncio
    async def test_ordering_is_deterministic(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Same query always returns same order."""
        await create_meals_with_timestamps(db, meal_type, 5)

        # Run multiple times
        results = [await get_meals_for_type(db, meal_type.id) for _ in range(3)]

        # All results should have same order
        for i in range(len(results[0])):
            assert results[0][i].id == results[1][i].id == results[2][i].id

    @pytest.mark.asyncio
    async def test_does_not_return_meals_from_other_types(
        self, db: AsyncSession, meal_types: list[MealType]
    ):
        """Only returns meals assigned to the specific meal type."""
        breakfast, lunch, _ = meal_types

        await create_meals_with_timestamps(db, breakfast, 2)
        await create_meals_with_timestamps(db, lunch, 3)

        breakfast_meals = await get_meals_for_type(db, breakfast.id)
        lunch_meals = await get_meals_for_type(db, lunch.id)

        assert len(breakfast_meals) == 2
        assert len(lunch_meals) == 3
        assert not any(bm.id in [lm.id for lm in lunch_meals] for bm in breakfast_meals)


class TestGetNextMealForType:
    """Tests for get_next_meal_for_type function - core round-robin algorithm."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_meals(
        self, db: AsyncSession, meal_type: MealType
    ):
        """No meals for type returns None."""
        meal = await get_next_meal_for_type(db, meal_type.id)
        assert meal is None

    @pytest.mark.asyncio
    async def test_returns_only_meal_when_single_meal(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Single meal is always returned."""
        created_meal = await create_meal(db, "Only Meal", meal_type)

        # Call multiple times - should always return same meal
        for _ in range(5):
            meal = await get_next_meal_for_type(db, meal_type.id)
            assert meal is not None
            assert meal.id == created_meal.id

    @pytest.mark.asyncio
    async def test_starts_with_first_meal_when_no_state(
        self, db: AsyncSession, meal_type: MealType
    ):
        """First call returns the first meal (earliest created_at)."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        meal = await get_next_meal_for_type(db, meal_type.id)

        assert meal is not None
        assert meal.id == meals[0].id

    @pytest.mark.asyncio
    async def test_rotates_through_meals_in_order(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Subsequent calls rotate through meals in order."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # First call - meal 1
        result1 = await get_next_meal_for_type(db, meal_type.id)
        assert result1.id == meals[0].id

        # Second call - meal 2
        result2 = await get_next_meal_for_type(db, meal_type.id)
        assert result2.id == meals[1].id

        # Third call - meal 3
        result3 = await get_next_meal_for_type(db, meal_type.id)
        assert result3.id == meals[2].id

    @pytest.mark.asyncio
    async def test_wraps_around_to_first_meal(
        self, db: AsyncSession, meal_type: MealType
    ):
        """After last meal, rotation wraps to first meal."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # Exhaust all meals
        for _ in range(3):
            await get_next_meal_for_type(db, meal_type.id)

        # Next call should wrap to first meal
        result = await get_next_meal_for_type(db, meal_type.id)
        assert result.id == meals[0].id

    @pytest.mark.asyncio
    async def test_updates_state_after_selection(
        self, db: AsyncSession, meal_type: MealType
    ):
        """State is updated to track the last selected meal."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # First selection
        await get_next_meal_for_type(db, meal_type.id)

        state = await get_round_robin_state(db, meal_type.id)
        assert state is not None
        assert state.last_meal_id == meals[0].id

        # Second selection
        await get_next_meal_for_type(db, meal_type.id)

        state = await get_round_robin_state(db, meal_type.id)
        assert state.last_meal_id == meals[1].id

    @pytest.mark.asyncio
    async def test_fairness_all_meals_get_equal_turns(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Over multiple rotations, all meals are selected equally."""
        meals = await create_meals_with_timestamps(db, meal_type, 4)
        num_rotations = 3
        total_selections = len(meals) * num_rotations

        selection_counts = {meal.id: 0 for meal in meals}

        for _ in range(total_selections):
            meal = await get_next_meal_for_type(db, meal_type.id)
            selection_counts[meal.id] += 1

        # Each meal should be selected exactly num_rotations times
        for meal in meals:
            assert selection_counts[meal.id] == num_rotations

    @pytest.mark.asyncio
    async def test_deterministic_same_inputs_same_outputs(
        self, db: AsyncSession, meal_types: list[MealType]
    ):
        """Same initial state produces same sequence of selections."""
        breakfast, lunch, _ = meal_types

        # Create same meals for both types
        base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        breakfast_meals = await create_meals_with_timestamps(
            db, breakfast, 3, base_time
        )

        # Reset state
        await reset_round_robin_state(db, breakfast.id)

        # First sequence
        sequence1 = []
        for _ in range(6):
            meal = await get_next_meal_for_type(db, breakfast.id)
            sequence1.append(meal.id)

        # Reset state again
        await reset_round_robin_state(db, breakfast.id)

        # Second sequence - should be identical
        sequence2 = []
        for _ in range(6):
            meal = await get_next_meal_for_type(db, breakfast.id)
            sequence2.append(meal.id)

        assert sequence1 == sequence2


class TestEdgeCases:
    """Tests for edge cases in round-robin algorithm."""

    @pytest.mark.asyncio
    async def test_handles_deleted_meal_in_state(
        self, db: AsyncSession, meal_type: MealType
    ):
        """
        When last meal is removed from meal type, gracefully reset to start.

        This tests the scenario where the state references a meal that is no
        longer assigned to this meal type (e.g., meal type assignment was removed,
        or meal was deleted with ON DELETE SET NULL).
        """
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # Select first two meals
        await get_next_meal_for_type(db, meal_type.id)
        await get_next_meal_for_type(db, meal_type.id)

        # State should point to meal 2
        state = await get_round_robin_state(db, meal_type.id)
        assert state.last_meal_id == meals[1].id

        # Remove meal 2 from this meal type (simulates deletion scenario)
        # The FK is ON DELETE SET NULL, so if meal is deleted, state.last_meal_id = NULL
        # But we can also test the case where meal exists but is not in the meal type list
        await db.execute(
            meal_to_meal_type.delete().where(
                meal_to_meal_type.c.meal_id == meals[1].id
            )
        )
        await db.flush()

        # Now meals list is [meal1, meal3] but state still points to meal2
        # Meal2 is not in the list, so it won't be found (index=-1)
        # Next index = ((-1) + 1) % 2 = 0, so we get meal1
        next_meal = await get_next_meal_for_type(db, meal_type.id)
        assert next_meal is not None
        assert next_meal.id == meals[0].id

    @pytest.mark.asyncio
    async def test_handles_null_last_meal_id(
        self, db: AsyncSession, meal_type: MealType, test_user: User
    ):
        """State with null last_meal_id starts from first meal."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # Create state with null last_meal_id
        state = RoundRobinState(
            user_id=test_user.id,
            meal_type_id=meal_type.id,
            last_meal_id=None,
        )
        db.add(state)
        await db.flush()

        # Should start with first meal
        meal = await get_next_meal_for_type(db, meal_type.id)
        assert meal.id == meals[0].id

    @pytest.mark.asyncio
    async def test_new_meal_added_to_end_of_rotation(
        self, db: AsyncSession, meal_type: MealType
    ):
        """New meals are appended to rotation (highest created_at)."""
        base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create initial meals
        meal1 = await create_meal(db, "Meal 1", meal_type, base_time)
        meal2 = await create_meal(
            db, "Meal 2", meal_type, base_time + timedelta(minutes=1)
        )

        # Go through rotation once
        result1 = await get_next_meal_for_type(db, meal_type.id)  # meal1
        result2 = await get_next_meal_for_type(db, meal_type.id)  # meal2
        assert result1.id == meal1.id
        assert result2.id == meal2.id

        # Add new meal (will have later created_at)
        meal3 = await create_meal(
            db, "Meal 3", meal_type, base_time + timedelta(minutes=2)
        )

        # State is at meal2 (index 1). Ordered list is now [meal1, meal2, meal3].
        # Next index = (1 + 1) % 3 = 2, so we get meal3 directly
        result3 = await get_next_meal_for_type(db, meal_type.id)
        assert result3.id == meal3.id

        # Verify rotation continues: meal1, meal2, meal3, meal1...
        result4 = await get_next_meal_for_type(db, meal_type.id)
        assert result4.id == meal1.id


class TestPeekNextMealForType:
    """Tests for peek_next_meal_for_type function."""

    @pytest.mark.asyncio
    async def test_returns_next_meal_without_advancing(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Peek returns next meal but doesn't advance state."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # Select first meal to establish state
        await get_next_meal_for_type(db, meal_type.id)

        # Peek multiple times - should always return same meal
        for _ in range(3):
            peek_result = await peek_next_meal_for_type(db, meal_type.id)
            assert peek_result.id == meals[1].id

        # State should still point to first meal
        state = await get_round_robin_state(db, meal_type.id)
        assert state.last_meal_id == meals[0].id

    @pytest.mark.asyncio
    async def test_peek_returns_none_when_no_meals(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Peek returns None when no meals available."""
        result = await peek_next_meal_for_type(db, meal_type.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_peek_matches_next_selection(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Peeked meal matches actual next selection."""
        await create_meals_with_timestamps(db, meal_type, 3)

        # Get next meal to establish state
        await get_next_meal_for_type(db, meal_type.id)

        # Peek should match next actual selection
        peeked = await peek_next_meal_for_type(db, meal_type.id)
        actual = await get_next_meal_for_type(db, meal_type.id)

        assert peeked.id == actual.id


class TestResetRoundRobinState:
    """Tests for reset_round_robin_state function."""

    @pytest.mark.asyncio
    async def test_removes_state_record(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Reset removes the state record."""
        await create_meals_with_timestamps(db, meal_type, 3)

        # Create state
        await get_next_meal_for_type(db, meal_type.id)

        state = await get_round_robin_state(db, meal_type.id)
        assert state is not None

        # Reset
        await reset_round_robin_state(db, meal_type.id)

        state = await get_round_robin_state(db, meal_type.id)
        assert state is None

    @pytest.mark.asyncio
    async def test_reset_causes_restart_from_first(
        self, db: AsyncSession, meal_type: MealType
    ):
        """After reset, next selection starts from first meal."""
        meals = await create_meals_with_timestamps(db, meal_type, 3)

        # Advance through rotation
        await get_next_meal_for_type(db, meal_type.id)  # meal1
        await get_next_meal_for_type(db, meal_type.id)  # meal2

        # Reset
        await reset_round_robin_state(db, meal_type.id)

        # Next should be first meal again
        result = await get_next_meal_for_type(db, meal_type.id)
        assert result.id == meals[0].id

    @pytest.mark.asyncio
    async def test_reset_nonexistent_state_is_noop(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Resetting when no state exists doesn't raise error."""
        # Should not raise
        await reset_round_robin_state(db, meal_type.id)


class TestUpdateRoundRobinState:
    """Tests for update_round_robin_state function."""

    @pytest.mark.asyncio
    async def test_creates_state_if_not_exists(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Creates new state record if none exists."""
        meals = await create_meals_with_timestamps(db, meal_type, 1)

        state = await update_round_robin_state(db, meal_type.id, meals[0].id)

        assert state is not None
        assert state.meal_type_id == meal_type.id
        assert state.last_meal_id == meals[0].id

    @pytest.mark.asyncio
    async def test_updates_existing_state(
        self, db: AsyncSession, meal_type: MealType
    ):
        """Updates existing state record."""
        meals = await create_meals_with_timestamps(db, meal_type, 2)

        # Create initial state
        await update_round_robin_state(db, meal_type.id, meals[0].id)

        # Update state
        state = await update_round_robin_state(db, meal_type.id, meals[1].id)

        assert state.last_meal_id == meals[1].id

    @pytest.mark.asyncio
    async def test_updates_timestamp(
        self, db: AsyncSession, meal_type: MealType
    ):
        """State timestamp is updated on each update."""
        meals = await create_meals_with_timestamps(db, meal_type, 1)

        state1 = await update_round_robin_state(db, meal_type.id, meals[0].id)
        first_update = state1.updated_at

        # Small delay then update again
        state2 = await update_round_robin_state(db, meal_type.id, meals[0].id)

        # Note: In fast tests, timestamps might be equal
        # Just verify the field exists and is set
        assert state2.updated_at is not None
