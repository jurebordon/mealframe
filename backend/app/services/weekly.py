"""
Service layer for weekly planning operations.

This module contains business logic for:
- Generating new weekly plan instances
- Switching day templates
- Managing day overrides
- Getting current/specific week plans

See Tech Spec sections 3.2 and 3.3 for algorithm specifications.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    WeekPlan,
    WeekPlanDay,
    DayTemplate,
    DayTemplateSlot,
    WeeklyPlanInstance,
    WeeklyPlanInstanceDay,
    WeeklyPlanSlot,
)
from .round_robin import get_next_meal_for_type


def get_week_start_date(target_date: date) -> date:
    """Get the Monday of the week containing the target date."""
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


def get_next_monday(from_date: date) -> date:
    """Get the next Monday after the given date.

    If from_date is Monday, returns the following Monday.
    """
    days_until_monday = (7 - from_date.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # If today is Monday, go to next Monday
    return from_date + timedelta(days=days_until_monday)


async def get_default_week_plan(db: AsyncSession, user_id: UUID) -> Optional[WeekPlan]:
    """Get the default week plan for a user."""
    stmt = (
        select(WeekPlan)
        .where(WeekPlan.is_default == True, WeekPlan.user_id == user_id)
        .options(selectinload(WeekPlan.days).selectinload(WeekPlanDay.day_template))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_week_plan_by_id(db: AsyncSession, week_plan_id: UUID) -> Optional[WeekPlan]:
    """Get a specific week plan by ID (internal use, no user_id filter)."""
    stmt = (
        select(WeekPlan)
        .where(WeekPlan.id == week_plan_id)
        .options(selectinload(WeekPlan.days).selectinload(WeekPlanDay.day_template))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_weekly_instance_by_week_start(
    db: AsyncSession, week_start_date: date, user_id: UUID,
) -> Optional[WeeklyPlanInstance]:
    """Get a weekly plan instance by its week start date, scoped to user."""
    stmt = select(WeeklyPlanInstance).where(
        WeeklyPlanInstance.week_start_date == week_start_date,
        WeeklyPlanInstance.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_day_template_by_id(db: AsyncSession, template_id: UUID) -> Optional[DayTemplate]:
    """Get a day template by ID with slots eagerly loaded (internal use)."""
    stmt = (
        select(DayTemplate)
        .where(DayTemplate.id == template_id)
        .options(selectinload(DayTemplate.slots).selectinload(DayTemplateSlot.meal_type))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def generate_weekly_plan(
    db: AsyncSession,
    week_start_date: Optional[date] = None,
    week_plan_id: Optional[UUID] = None,
    user_id: UUID = None,
) -> WeeklyPlanInstance:
    """
    Generate a new weekly plan instance.

    Args:
        db: Database session
        week_start_date: Monday of the target week. Defaults to next Monday if not provided.
        week_plan_id: Optional specific plan to use; uses default if not provided.
        user_id: UUID of the authenticated user.

    Process (per Tech Spec section 3.2):
        1. Create weekly_plan_instance record
        2. For each day (Mon-Sun):
           a. Get day template from week plan
           b. Create weekly_plan_instance_day record
           c. For each slot in template:
              - Get next meal via round-robin
              - Create weekly_plan_slot record

    Returns:
        Complete WeeklyPlanInstance with all relations loaded

    Raises:
        ValueError: If no week plan available or week already exists
    """
    # Determine week start date
    if week_start_date is None:
        week_start_date = get_next_monday(date.today())

    # Validate it's a Monday
    if week_start_date.weekday() != 0:
        raise ValueError(f"week_start_date must be a Monday, got {week_start_date}")

    # Check for existing instance
    existing = await get_weekly_instance_by_week_start(db, week_start_date, user_id)
    if existing:
        raise ValueError(f"Week starting {week_start_date} already exists")

    # Get week plan
    if week_plan_id:
        week_plan = await get_week_plan_by_id(db, week_plan_id)
        if not week_plan:
            raise ValueError(f"Week plan with id {week_plan_id} not found")
    else:
        week_plan = await get_default_week_plan(db, user_id)
        if not week_plan:
            raise ValueError("No default week plan available")

    # Create instance
    instance = WeeklyPlanInstance(
        week_plan_id=week_plan.id,
        week_start_date=week_start_date,
        user_id=user_id,
    )
    db.add(instance)
    await db.flush()

    # Build day map from week plan
    day_map = {wpd.weekday: wpd.day_template_id for wpd in week_plan.days}

    # Generate each day
    for day_offset in range(7):
        current_date = week_start_date + timedelta(days=day_offset)
        weekday = day_offset  # 0=Monday

        template_id = day_map.get(weekday)
        if not template_id:
            # No template for this day - skip (shouldn't happen with complete week plan)
            continue

        # Create day record
        instance_day = WeeklyPlanInstanceDay(
            weekly_plan_instance_id=instance.id,
            date=current_date,
            day_template_id=template_id,
            is_override=False,
        )
        db.add(instance_day)

        # Get template with slots
        template = await get_day_template_by_id(db, template_id)
        if not template:
            continue

        # Sort slots by position
        slots = sorted(template.slots, key=lambda s: s.position)

        # Generate meal for each slot
        for slot in slots:
            meal = await get_next_meal_for_type(db, slot.meal_type_id)

            plan_slot = WeeklyPlanSlot(
                weekly_plan_instance_id=instance.id,
                date=current_date,
                position=slot.position,
                meal_type_id=slot.meal_type_id,
                meal_id=meal.id if meal else None,
                completion_status=None,
                completed_at=None,
            )
            db.add(plan_slot)

    await db.flush()
    return instance


async def get_current_week_instance(db: AsyncSession, user_id: UUID) -> Optional[WeeklyPlanInstance]:
    """Get the weekly plan instance for the current week, scoped to user."""
    week_start = get_week_start_date(date.today())
    return await get_weekly_instance_by_week_start(db, week_start, user_id)


async def get_week_instance(
    db: AsyncSession, user_id: UUID, week_start_date: Optional[date] = None,
) -> Optional[WeeklyPlanInstance]:
    """Get the weekly plan instance for a specific week or current week if not specified."""
    if week_start_date is None:
        week_start = get_week_start_date(date.today())
    else:
        # Normalize to Monday if not already
        week_start = get_week_start_date(week_start_date)
    return await get_weekly_instance_by_week_start(db, week_start, user_id)


async def get_full_weekly_instance(
    db: AsyncSession, instance_id: UUID
) -> Optional[WeeklyPlanInstance]:
    """Get a weekly instance with all relations eagerly loaded."""
    stmt = (
        select(WeeklyPlanInstance)
        .where(WeeklyPlanInstance.id == instance_id)
        .options(
            selectinload(WeeklyPlanInstance.week_plan),
            selectinload(WeeklyPlanInstance.days).selectinload(
                WeeklyPlanInstanceDay.day_template
            ),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_slots_for_instance_day(
    db: AsyncSession, instance_id: UUID, target_date: date
) -> list[WeeklyPlanSlot]:
    """Get all slots for a specific day in an instance."""
    stmt = (
        select(WeeklyPlanSlot)
        .where(
            and_(
                WeeklyPlanSlot.weekly_plan_instance_id == instance_id,
                WeeklyPlanSlot.date == target_date,
            )
        )
        .options(
            selectinload(WeeklyPlanSlot.meal),
            selectinload(WeeklyPlanSlot.meal_type),
            selectinload(WeeklyPlanSlot.actual_meal),
        )
        .order_by(WeeklyPlanSlot.position)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_instance_day(
    db: AsyncSession, instance_id: UUID, target_date: date
) -> Optional[WeeklyPlanInstanceDay]:
    """Get the instance day record for a specific date."""
    stmt = (
        select(WeeklyPlanInstanceDay)
        .where(
            and_(
                WeeklyPlanInstanceDay.weekly_plan_instance_id == instance_id,
                WeeklyPlanInstanceDay.date == target_date,
            )
        )
        .options(selectinload(WeeklyPlanInstanceDay.day_template))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def switch_day_template(
    db: AsyncSession,
    instance_id: UUID,
    target_date: date,
    new_template_id: UUID,
) -> WeeklyPlanInstanceDay:
    """
    Switch a day's template and regenerate its slots.

    Per Tech Spec section 3.3:
        1. Delete existing slots for the day
        2. Update instance_day record with new template
        3. Generate new slots with round-robin meals

    Note: Completion statuses are lost when switching.

    Args:
        db: Database session
        instance_id: UUID of the weekly plan instance
        target_date: The date to switch
        new_template_id: UUID of the new day template

    Returns:
        Updated WeeklyPlanInstanceDay

    Raises:
        ValueError: If instance day or template not found
    """
    # Get instance day
    instance_day = await get_instance_day(db, instance_id, target_date)
    if not instance_day:
        raise ValueError(f"No day record for {target_date}")

    # Verify template exists
    template = await get_day_template_by_id(db, new_template_id)
    if not template:
        raise ValueError(f"Day template with id {new_template_id} not found")

    # Delete existing slots for this day
    delete_stmt = delete(WeeklyPlanSlot).where(
        and_(
            WeeklyPlanSlot.weekly_plan_instance_id == instance_id,
            WeeklyPlanSlot.date == target_date,
        )
    )
    await db.execute(delete_stmt)

    # Update instance day with new template
    instance_day.day_template_id = new_template_id
    instance_day.is_override = False
    instance_day.override_reason = None
    instance_day.updated_at = datetime.now(timezone.utc)

    # Get template slots ordered by position
    slots = sorted(template.slots, key=lambda s: s.position)

    # Generate new meals for each slot
    for slot in slots:
        meal = await get_next_meal_for_type(db, slot.meal_type_id)

        plan_slot = WeeklyPlanSlot(
            weekly_plan_instance_id=instance_id,
            date=target_date,
            position=slot.position,
            meal_type_id=slot.meal_type_id,
            meal_id=meal.id if meal else None,
            completion_status=None,
            completed_at=None,
        )
        db.add(plan_slot)

    await db.flush()

    # Refresh to get updated relationships
    await db.refresh(instance_day)
    return instance_day


async def set_day_override(
    db: AsyncSession,
    instance_id: UUID,
    target_date: date,
    reason: Optional[str] = None,
) -> WeeklyPlanInstanceDay:
    """
    Mark a day as "no plan" override.

    Deletes existing slots and marks the day as override.

    Args:
        db: Database session
        instance_id: UUID of the weekly plan instance
        target_date: The date to override
        reason: Optional reason for the override

    Returns:
        Updated WeeklyPlanInstanceDay

    Raises:
        ValueError: If instance day not found
    """
    # Get instance day
    instance_day = await get_instance_day(db, instance_id, target_date)
    if not instance_day:
        raise ValueError(f"No day record for {target_date}")

    # Delete existing slots for this day
    delete_stmt = delete(WeeklyPlanSlot).where(
        and_(
            WeeklyPlanSlot.weekly_plan_instance_id == instance_id,
            WeeklyPlanSlot.date == target_date,
        )
    )
    await db.execute(delete_stmt)

    # Mark day as override
    instance_day.is_override = True
    instance_day.override_reason = reason
    instance_day.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return instance_day


async def clear_day_override(
    db: AsyncSession,
    instance_id: UUID,
    target_date: date,
) -> WeeklyPlanInstanceDay:
    """
    Remove override and restore plan for a day.

    Regenerates slots using the day's template.

    Args:
        db: Database session
        instance_id: UUID of the weekly plan instance
        target_date: The date to restore

    Returns:
        Updated WeeklyPlanInstanceDay with restored slots

    Raises:
        ValueError: If instance day not found or no template available
    """
    # Get instance day
    instance_day = await get_instance_day(db, instance_id, target_date)
    if not instance_day:
        raise ValueError(f"No day record for {target_date}")

    if not instance_day.day_template_id:
        raise ValueError(f"No template available for {target_date}")

    # Get the template
    template = await get_day_template_by_id(db, instance_day.day_template_id)
    if not template:
        raise ValueError(f"Template {instance_day.day_template_id} not found")

    # Clear override flag
    instance_day.is_override = False
    instance_day.override_reason = None
    instance_day.updated_at = datetime.now(timezone.utc)

    # Get template slots ordered by position
    slots = sorted(template.slots, key=lambda s: s.position)

    # Generate new meals for each slot
    for slot in slots:
        meal = await get_next_meal_for_type(db, slot.meal_type_id)

        plan_slot = WeeklyPlanSlot(
            weekly_plan_instance_id=instance_id,
            date=target_date,
            position=slot.position,
            meal_type_id=slot.meal_type_id,
            meal_id=meal.id if meal else None,
            completion_status=None,
            completed_at=None,
        )
        db.add(plan_slot)

    await db.flush()
    return instance_day


def is_date_in_week(target_date: date, week_start: date) -> bool:
    """Check if a date falls within the week starting at week_start."""
    week_end = week_start + timedelta(days=6)
    return week_start <= target_date <= week_end


async def regenerate_weekly_plan(
    db: AsyncSession,
    week_start_date: date,
    user_id: UUID,
) -> WeeklyPlanInstance:
    """
    Regenerate uncompleted slots in an existing weekly plan.

    Only regenerates slots that:
    1. Have no completion_status (uncompleted)
    2. Are in the future OR are today but not yet completed

    Preserves all completed slots and their meal assignments.

    Args:
        db: Database session
        week_start_date: Monday of the target week
        user_id: UUID of the authenticated user

    Returns:
        Updated WeeklyPlanInstance

    Raises:
        ValueError: If week doesn't exist or invalid date
    """
    # Validate it's a Monday
    week_start = get_week_start_date(week_start_date)
    if week_start != week_start_date:
        # Auto-correct to Monday of that week
        week_start_date = week_start

    # Get existing instance
    instance = await get_weekly_instance_by_week_start(db, week_start_date, user_id)
    if not instance:
        raise ValueError(f"No week plan exists for week starting {week_start_date}")

    # Get full instance with days
    full_instance = await get_full_weekly_instance(db, instance.id)
    if not full_instance:
        raise ValueError(f"Could not load week plan for {week_start_date}")

    today = date.today()

    # For each day, regenerate uncompleted slots
    for instance_day in full_instance.days:
        # Skip override days (no meals to regenerate)
        if instance_day.is_override:
            continue

        # Skip if no template
        if not instance_day.day_template_id:
            continue

        # Get current slots for this day
        current_slots = await get_slots_for_instance_day(db, instance.id, instance_day.date)

        # Find uncompleted slots (completion_status is NULL)
        uncompleted_slots = [s for s in current_slots if s.completion_status is None]

        if not uncompleted_slots:
            # All slots are completed, nothing to regenerate
            continue

        # Get the template with its slots
        template = await get_day_template_by_id(db, instance_day.day_template_id)
        if not template:
            continue

        # Build a map of template slot positions to meal types
        template_slots_by_position = {ts.position: ts for ts in template.slots}

        # Regenerate each uncompleted slot with a new meal
        for slot in uncompleted_slots:
            template_slot = template_slots_by_position.get(slot.position)
            if not template_slot:
                continue

            # Get a new meal via round-robin
            new_meal = await get_next_meal_for_type(db, template_slot.meal_type_id)

            # Update the slot with new meal
            slot.meal_id = new_meal.id if new_meal else None
            slot.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return instance
