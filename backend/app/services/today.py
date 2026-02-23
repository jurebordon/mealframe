"""
Service layer for Today/Yesterday view operations.

This module contains business logic for:
- Fetching today's or any day's meal plan
- Computing is_next indicator for slots
- Calculating streak statistics
- Managing slot completion status
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    WeeklyPlanInstance,
    WeeklyPlanInstanceDay,
    WeeklyPlanSlot,
    DayTemplate,
    MealType,
    Meal,
)
from ..models.meal_to_meal_type import meal_to_meal_type
from ..schemas.common import WEEKDAY_NAMES
from ..schemas.today import TodayResponse, TodayStats
from ..schemas.weekly_plan import WeeklyPlanSlotWithNext
from ..schemas.day_template import DayTemplateCompact
from ..schemas.meal import MealCompact
from ..schemas.meal_type import MealTypeCompact


async def get_week_start_date(target_date: date) -> date:
    """Get the Monday of the week containing the target date."""
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


async def get_day_plan(
    db: AsyncSession,
    target_date: date,
) -> Optional[tuple[WeeklyPlanInstanceDay, list[WeeklyPlanSlot]]]:
    """
    Get the plan for a specific day.

    Returns tuple of (instance_day, slots) if a plan exists, None otherwise.
    """
    # Find the weekly instance containing this date
    week_start = await get_week_start_date(target_date)

    stmt = select(WeeklyPlanInstance).where(
        WeeklyPlanInstance.week_start_date == week_start
    )
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        return None

    # Get the day record
    day_stmt = select(WeeklyPlanInstanceDay).where(
        and_(
            WeeklyPlanInstanceDay.weekly_plan_instance_id == instance.id,
            WeeklyPlanInstanceDay.date == target_date,
        )
    ).options(selectinload(WeeklyPlanInstanceDay.day_template))

    day_result = await db.execute(day_stmt)
    instance_day = day_result.scalar_one_or_none()

    if not instance_day:
        return None

    # Get slots for this day with meal and meal_type eagerly loaded
    slots_stmt = (
        select(WeeklyPlanSlot)
        .where(
            and_(
                WeeklyPlanSlot.weekly_plan_instance_id == instance.id,
                WeeklyPlanSlot.date == target_date,
            )
        )
        .options(
            selectinload(WeeklyPlanSlot.meal),
            selectinload(WeeklyPlanSlot.meal_type),
        )
        .order_by(WeeklyPlanSlot.position)
    )

    slots_result = await db.execute(slots_stmt)
    slots = list(slots_result.scalars().all())

    return (instance_day, slots)


async def calculate_streak(db: AsyncSession, target_date: date) -> int:
    """
    Calculate the current streak of consecutive days with all meals completed.

    A day counts toward the streak if:
    - It has slots with a plan
    - All slots have a completion_status (not NULL)

    Override days count toward the streak (plan changes are fine).
    We count backwards from the day before target_date.
    """
    streak = 0
    check_date = target_date - timedelta(days=1)

    while True:
        day_plan = await get_day_plan(db, check_date)

        if not day_plan:
            # No plan for this day - streak ends
            break

        instance_day, slots = day_plan

        if not slots:
            # No meals - streak ends
            break

        # Check if all slots are completed
        all_completed = all(slot.completion_status is not None for slot in slots)

        if not all_completed:
            break

        streak += 1
        check_date -= timedelta(days=1)

        # Safety limit to avoid infinite loops
        if streak > 365:
            break

    return streak


def build_today_response(
    target_date: date,
    instance_day: Optional[WeeklyPlanInstanceDay],
    slots: list[WeeklyPlanSlot],
    streak: int,
) -> TodayResponse:
    """
    Build a TodayResponse from the day data.

    Computes is_next for slots and builds stats.
    """
    weekday_name = WEEKDAY_NAMES.get(target_date.weekday(), "Unknown")

    # Handle case with no plan
    if instance_day is None:
        return TodayResponse(
            date=target_date,
            weekday=weekday_name,
            template=None,
            is_override=False,
            override_reason=None,
            slots=[],
            stats=TodayStats(completed=0, total=0, streak_days=streak),
        )

    # Build template compact
    template_compact = None
    if instance_day.day_template:
        template_compact = DayTemplateCompact(
            id=instance_day.day_template.id,
            name=instance_day.day_template.name,
        )

    # Find the first incomplete slot (is_next indicator)
    first_incomplete_index = None
    for i, slot in enumerate(slots):
        if slot.completion_status is None:
            first_incomplete_index = i
            break

    # Build slot responses
    slot_responses = []
    completed_count = 0

    for i, slot in enumerate(slots):
        is_next = (i == first_incomplete_index)

        if slot.completion_status is not None:
            completed_count += 1

        # Build meal compact
        meal_compact = None
        if slot.meal:
            meal_compact = MealCompact(
                id=slot.meal.id,
                name=slot.meal.name,
                portion_description=slot.meal.portion_description,
                calories_kcal=slot.meal.calories_kcal,
                protein_g=slot.meal.protein_g,
                carbs_g=slot.meal.carbs_g,
                sugar_g=slot.meal.sugar_g,
                fat_g=slot.meal.fat_g,
                saturated_fat_g=slot.meal.saturated_fat_g,
                fiber_g=slot.meal.fiber_g,
            )

        # Build meal type compact
        meal_type_compact = None
        if slot.meal_type:
            meal_type_compact = MealTypeCompact(
                id=slot.meal_type.id,
                name=slot.meal_type.name,
            )

        slot_responses.append(WeeklyPlanSlotWithNext(
            id=slot.id,
            position=slot.position,
            meal_type=meal_type_compact,
            meal=meal_compact,
            completion_status=slot.completion_status,
            completed_at=slot.completed_at,
            is_next=is_next,
            is_adhoc=slot.is_adhoc,
            is_manual_override=slot.is_manual_override,
        ))

    return TodayResponse(
        date=target_date,
        weekday=weekday_name,
        template=template_compact,
        is_override=instance_day.is_override,
        override_reason=instance_day.override_reason,
        slots=slot_responses,
        stats=TodayStats(
            completed=completed_count,
            total=len(slots),
            streak_days=streak,
        ),
    )


async def get_today_response(
    db: AsyncSession,
    target_date: date,
) -> TodayResponse:
    """
    Get the full TodayResponse for a specific date.

    This is the main entry point for GET /today and GET /yesterday.
    """
    day_plan = await get_day_plan(db, target_date)
    streak = await calculate_streak(db, target_date)

    if day_plan:
        instance_day, slots = day_plan
        return build_today_response(target_date, instance_day, slots, streak)
    else:
        return build_today_response(target_date, None, [], streak)


async def get_slot_by_id(
    db: AsyncSession,
    slot_id: UUID,
) -> Optional[WeeklyPlanSlot]:
    """Get a slot by its ID."""
    stmt = select(WeeklyPlanSlot).where(WeeklyPlanSlot.id == slot_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def complete_slot(
    db: AsyncSession,
    slot_id: UUID,
    status: str,
) -> Optional[WeeklyPlanSlot]:
    """
    Mark a slot as complete with the given status.

    Returns the updated slot, or None if slot not found.
    """
    slot = await get_slot_by_id(db, slot_id)

    if not slot:
        return None

    slot.completion_status = status
    slot.completed_at = datetime.now(timezone.utc)

    await db.flush()
    return slot


async def uncomplete_slot(
    db: AsyncSession,
    slot_id: UUID,
) -> Optional[WeeklyPlanSlot]:
    """
    Undo completion of a slot (reset to NULL).

    Returns the updated slot, or None if slot not found.
    """
    slot = await get_slot_by_id(db, slot_id)

    if not slot:
        return None

    slot.completion_status = None
    slot.completed_at = None

    await db.flush()
    return slot


async def create_adhoc_slot(
    db: AsyncSession,
    target_date: date,
    meal_id: UUID,
) -> Optional[WeeklyPlanSlot]:
    """
    Create an ad-hoc meal slot for the given date.

    Finds the weekly plan instance for the date, determines the next position,
    and creates a new slot with is_adhoc=True. Copies the meal's first
    associated meal type (if any).

    Returns the created slot, or None if no weekly plan instance exists for the date.
    """
    # Find the weekly instance
    week_start = await get_week_start_date(target_date)
    stmt = select(WeeklyPlanInstance).where(
        WeeklyPlanInstance.week_start_date == week_start
    )
    result = await db.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        return None

    # Get the meal (with its types)
    meal_stmt = (
        select(Meal)
        .where(Meal.id == meal_id)
        .options(selectinload(Meal.meal_types))
    )
    meal_result = await db.execute(meal_stmt)
    meal = meal_result.scalar_one_or_none()

    if not meal:
        return None

    # Determine next position (max existing + 1)
    max_pos_stmt = select(func.coalesce(func.max(WeeklyPlanSlot.position), -1)).where(
        and_(
            WeeklyPlanSlot.weekly_plan_instance_id == instance.id,
            WeeklyPlanSlot.date == target_date,
        )
    )
    max_pos_result = await db.execute(max_pos_stmt)
    max_position = max_pos_result.scalar()
    next_position = max_position + 1

    # Get first meal type (if any)
    first_meal_type_id = None
    if meal.meal_types:
        first_meal_type_id = meal.meal_types[0].id

    # Create the ad-hoc slot
    slot = WeeklyPlanSlot(
        weekly_plan_instance_id=instance.id,
        date=target_date,
        position=next_position,
        meal_type_id=first_meal_type_id,
        meal_id=meal_id,
        is_adhoc=True,
    )
    db.add(slot)
    await db.flush()

    # Eagerly load relationships for the response
    await db.refresh(slot, attribute_names=["meal", "meal_type"])

    return slot


async def delete_adhoc_slot(
    db: AsyncSession,
    slot_id: UUID,
) -> Optional[bool]:
    """
    Delete an ad-hoc slot.

    Returns True if deleted, False if the slot exists but is not ad-hoc,
    or None if the slot doesn't exist.
    """
    slot = await get_slot_by_id(db, slot_id)

    if not slot:
        return None

    if not slot.is_adhoc:
        return False

    await db.delete(slot)
    await db.flush()
    return True


async def reassign_slot(
    db: AsyncSession,
    slot_id: UUID,
    meal_id: UUID,
    meal_type_id: UUID | None = None,
) -> tuple[str | None, Optional[WeeklyPlanSlot]]:
    """
    Reassign a slot to a different meal.

    Returns (error_message, slot). If error_message is not None, slot is None.
    Does NOT advance round-robin pointer.
    Clears completion status if slot was already completed.
    """
    # Get the slot with relationships loaded
    stmt = (
        select(WeeklyPlanSlot)
        .where(WeeklyPlanSlot.id == slot_id)
        .options(
            selectinload(WeeklyPlanSlot.meal),
            selectinload(WeeklyPlanSlot.meal_type),
        )
    )
    result = await db.execute(stmt)
    slot = result.scalar_one_or_none()

    if not slot:
        return ("NOT_FOUND", None)

    # Don't allow reassigning past-date slots
    today = date.today()
    if slot.date < today:
        return ("PAST_DATE", None)

    # Verify meal exists
    meal_stmt = select(Meal).where(Meal.id == meal_id)
    meal_result = await db.execute(meal_stmt)
    meal = meal_result.scalar_one_or_none()

    if not meal:
        return ("MEAL_NOT_FOUND", None)

    # Determine target meal type
    target_meal_type_id = meal_type_id if meal_type_id is not None else slot.meal_type_id

    # Verify meal belongs to target meal type (if a meal type is set)
    if target_meal_type_id is not None:
        assoc_stmt = select(meal_to_meal_type).where(
            and_(
                meal_to_meal_type.c.meal_id == meal_id,
                meal_to_meal_type.c.meal_type_id == target_meal_type_id,
            )
        )
        assoc_result = await db.execute(assoc_stmt)
        if not assoc_result.first():
            return ("MEAL_TYPE_MISMATCH", None)

    # Apply the reassignment
    slot.meal_id = meal_id
    if meal_type_id is not None:
        slot.meal_type_id = meal_type_id
    slot.is_manual_override = True

    # Clear completion if already completed (new meal = fresh tracking)
    if slot.completion_status is not None:
        slot.completion_status = None
        slot.completed_at = None

    await db.flush()

    # Refresh relationships for response
    await db.refresh(slot, attribute_names=["meal", "meal_type"])

    return (None, slot)
