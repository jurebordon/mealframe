"""
Round-robin meal selection algorithm.

This module implements the deterministic round-robin algorithm for selecting
meals from a meal type. The algorithm ensures fair rotation of meals and
provides variety without requiring user decisions.

Key properties (ADR-002):
- Deterministic: Same inputs always produce same outputs
- Fair: Every meal gets equal rotation
- Extensible: New meals automatically enter rotation
- Resilient: Deleted meals don't break state

See Tech Spec section 3.1 for full specification.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Meal, MealType, RoundRobinState
from ..models.meal_to_meal_type import meal_to_meal_type


async def get_meals_for_type(
    db: AsyncSession,
    meal_type_id: UUID,
) -> list[Meal]:
    """
    Get all meals for a meal type, deterministically ordered.

    Ordering: (created_at ASC, id ASC) ensures consistent results
    across all invocations with the same data.

    Args:
        db: Database session
        meal_type_id: UUID of the meal type

    Returns:
        List of Meal objects ordered by (created_at, id)
    """
    stmt = (
        select(Meal)
        .join(meal_to_meal_type, Meal.id == meal_to_meal_type.c.meal_id)
        .where(meal_to_meal_type.c.meal_type_id == meal_type_id)
        .order_by(Meal.created_at.asc(), Meal.id.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_round_robin_state(
    db: AsyncSession,
    meal_type_id: UUID,
    user_id: Optional[UUID] = None,
) -> Optional[RoundRobinState]:
    """
    Get the current round-robin state for a meal type.

    Args:
        db: Database session
        meal_type_id: UUID of the meal type
        user_id: UUID of the user (optional, will filter by user if provided)

    Returns:
        RoundRobinState if exists, None otherwise
    """
    stmt = select(RoundRobinState).where(
        RoundRobinState.meal_type_id == meal_type_id
    )
    if user_id is not None:
        stmt = stmt.where(RoundRobinState.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_user_id_for_meal_type(db: AsyncSession, meal_type_id: UUID) -> UUID:
    """Look up the user_id for a meal type."""
    stmt = select(MealType.user_id).where(MealType.id == meal_type_id)
    result = await db.execute(stmt)
    user_id = result.scalar_one_or_none()
    if user_id is None:
        raise ValueError(f"MealType {meal_type_id} not found")
    return user_id


async def update_round_robin_state(
    db: AsyncSession,
    meal_type_id: UUID,
    meal_id: UUID,
) -> RoundRobinState:
    """
    Update or create the round-robin state for a meal type.

    This is an upsert operation: if state exists, it's updated;
    otherwise, a new state record is created. The user_id is derived
    from the meal type's owner.

    Args:
        db: Database session
        meal_type_id: UUID of the meal type
        meal_id: UUID of the meal just selected

    Returns:
        The updated or created RoundRobinState
    """
    state = await get_round_robin_state(db, meal_type_id)

    now = datetime.now(timezone.utc)

    if state:
        state.last_meal_id = meal_id
        state.updated_at = now
    else:
        user_id = await _get_user_id_for_meal_type(db, meal_type_id)
        state = RoundRobinState(
            user_id=user_id,
            meal_type_id=meal_type_id,
            last_meal_id=meal_id,
            updated_at=now,
        )
        db.add(state)

    await db.flush()
    return state


async def get_next_meal_for_type(
    db: AsyncSession,
    meal_type_id: UUID,
) -> Optional[Meal]:
    """
    Select the next meal for a meal type using round-robin rotation.

    This is the core algorithm that provides deterministic meal selection:
    1. Get all meals for the type, ordered by (created_at ASC, id ASC)
    2. Find the last-used meal from round-robin state
    3. Return the next meal in sequence (wrapping to start if needed)
    4. Update state with the selected meal

    Edge cases handled:
    - No meals: Returns None
    - One meal: Always returns that meal
    - Deleted meal in state: Resets to first meal (graceful degradation)
    - New meal added: Appended to rotation (highest created_at)
    - No state: Starts with first meal

    Args:
        db: Database session
        meal_type_id: UUID of the meal type

    Returns:
        The next Meal in rotation, or None if no meals available
    """
    meals = await get_meals_for_type(db, meal_type_id)

    if not meals:
        return None

    if len(meals) == 1:
        # Single meal - always return it, update state
        await update_round_robin_state(db, meal_type_id, meals[0].id)
        return meals[0]

    # Get current state
    state = await get_round_robin_state(db, meal_type_id)

    if state is None or state.last_meal_id is None:
        # No state - start with first meal
        next_meal = meals[0]
    else:
        # Find index of last used meal
        last_index = -1
        for i, meal in enumerate(meals):
            if meal.id == state.last_meal_id:
                last_index = i
                break

        # Compute next index:
        # - If last meal was deleted (not found, last_index=-1), next_index becomes 0
        # - Otherwise, advance to next meal with wraparound
        next_index = (last_index + 1) % len(meals)
        next_meal = meals[next_index]

    # Update state with selected meal
    await update_round_robin_state(db, meal_type_id, next_meal.id)

    return next_meal


async def peek_next_meal_for_type(
    db: AsyncSession,
    meal_type_id: UUID,
) -> Optional[Meal]:
    """
    Preview the next meal for a meal type WITHOUT advancing the state.

    This is useful for displaying what the next meal would be without
    actually committing to that selection. The state remains unchanged.

    Args:
        db: Database session
        meal_type_id: UUID of the meal type

    Returns:
        The next Meal in rotation, or None if no meals available
    """
    meals = await get_meals_for_type(db, meal_type_id)

    if not meals:
        return None

    if len(meals) == 1:
        return meals[0]

    state = await get_round_robin_state(db, meal_type_id)

    if state is None or state.last_meal_id is None:
        return meals[0]

    # Find index of last used meal
    last_index = -1
    for i, meal in enumerate(meals):
        if meal.id == state.last_meal_id:
            last_index = i
            break

    next_index = (last_index + 1) % len(meals)
    return meals[next_index]


async def reset_round_robin_state(
    db: AsyncSession,
    meal_type_id: UUID,
    user_id: Optional[UUID] = None,
) -> None:
    """
    Reset the round-robin state for a meal type.

    This removes the state record, causing the next selection to start
    from the first meal in the rotation.

    Args:
        db: Database session
        meal_type_id: UUID of the meal type
        user_id: UUID of the user (optional)
    """
    state = await get_round_robin_state(db, meal_type_id, user_id=user_id)
    if state:
        await db.delete(state)
        await db.flush()
