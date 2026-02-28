"""
Service layer for week plan operations.

Handles CRUD operations for week plans (templates, not instances).
Per Tech Spec section 4.5 (Setup/Admin Endpoints).
"""
import logging
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.week_plan import WeekPlan, WeekPlanDay
from app.schemas.week_plan import WeekPlanCreate, WeekPlanDayCreate, WeekPlanUpdate

logger = logging.getLogger(__name__)


async def list_week_plans(db: AsyncSession, user_id: UUID) -> list[dict]:
    """
    List all week plans with day counts, scoped to user.

    Returns list of dicts with WeekPlan objects and day_count.
    """
    result = await db.execute(
        select(WeekPlan)
        .options(selectinload(WeekPlan.days))
        .where(WeekPlan.user_id == user_id)
        .order_by(WeekPlan.name)
    )
    plans = result.scalars().unique().all()

    return [
        {"plan": plan, "day_count": len(plan.days)}
        for plan in plans
    ]


async def get_week_plan_by_id(db: AsyncSession, plan_id: UUID, user_id: UUID) -> WeekPlan | None:
    """Get a single week plan by ID with days and day templates eagerly loaded.
    Returns None if not owned by user."""
    result = await db.execute(
        select(WeekPlan)
        .options(
            selectinload(WeekPlan.days).selectinload(WeekPlanDay.day_template)
        )
        .where(WeekPlan.id == plan_id, WeekPlan.user_id == user_id)
    )
    return result.scalars().first()


async def create_week_plan(db: AsyncSession, data: WeekPlanCreate, user_id: UUID) -> WeekPlan:
    """Create a new week plan with day mappings."""
    # Check if this is the first week plan for this user
    count_result = await db.execute(
        select(func.count(WeekPlan.id)).where(WeekPlan.user_id == user_id)
    )
    existing_count = count_result.scalar() or 0

    # Auto-default the first week plan
    is_default = data.is_default
    if existing_count == 0:
        is_default = True

    # If this is set as default, clear other defaults for this user
    if is_default:
        await _clear_default(db, user_id)

    plan = WeekPlan(
        name=data.name,
        is_default=is_default,
        user_id=user_id,
    )
    db.add(plan)
    await db.flush()

    # Create day mappings
    await _replace_days(db, plan.id, data.days)

    # Reload with relationships
    return await get_week_plan_by_id(db, plan.id, user_id)


async def update_week_plan(
    db: AsyncSession, plan: WeekPlan, data: WeekPlanUpdate
) -> WeekPlan:
    """Update an existing week plan. Only non-None fields are updated."""
    if data.name is not None:
        plan.name = data.name

    if data.is_default is not None:
        if data.is_default:
            await _clear_default(db, plan.user_id)
        plan.is_default = data.is_default

    # Replace day mappings if provided
    if data.days is not None:
        await _replace_days(db, plan.id, data.days)

    await db.flush()

    # Capture ID and user_id before expunging
    plan_id = plan.id
    plan_user_id = plan.user_id
    db.expunge(plan)

    # Reload with fresh relationships
    return await get_week_plan_by_id(db, plan_id, plan_user_id)


async def delete_week_plan(db: AsyncSession, plan: WeekPlan) -> None:
    """Delete a week plan. Cascades to week_plan_days."""
    await db.delete(plan)
    await db.flush()


async def set_default_week_plan(db: AsyncSession, plan: WeekPlan) -> WeekPlan:
    """Set a week plan as the default, clearing any other defaults for this user."""
    await _clear_default(db, plan.user_id)
    plan.is_default = True
    await db.flush()
    return await get_week_plan_by_id(db, plan.id, plan.user_id)


async def _clear_default(db: AsyncSession, user_id: UUID) -> None:
    """Clear the is_default flag on all week plans for the given user."""
    result = await db.execute(
        select(WeekPlan).where(WeekPlan.is_default == True, WeekPlan.user_id == user_id)
    )
    for plan in result.scalars().all():
        plan.is_default = False
    await db.flush()


async def _replace_days(
    db: AsyncSession,
    plan_id: UUID,
    days: list[WeekPlanDayCreate],
) -> None:
    """Delete existing day mappings and create new ones for a week plan."""
    # Delete existing days
    await db.execute(
        delete(WeekPlanDay).where(WeekPlanDay.week_plan_id == plan_id)
    )

    # Create new day mappings
    for day_data in days:
        day = WeekPlanDay(
            week_plan_id=plan_id,
            weekday=day_data.weekday,
            day_template_id=day_data.day_template_id,
        )
        db.add(day)

    await db.flush()
