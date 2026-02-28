"""
API routes for week plan template endpoints.

Provides CRUD operations for week plans (templates, not generated instances).
Per Tech Spec section 4.5 (Setup/Admin Endpoints).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.week_plan import (
    WeekPlanCreate,
    WeekPlanDayResponse,
    WeekPlanListItem,
    WeekPlanResponse,
    WeekPlanUpdate,
)
from ..schemas.day_template import DayTemplateCompact
from ..schemas.common import WEEKDAY_NAMES
from ..services.week_plans import (
    create_week_plan,
    delete_week_plan,
    get_week_plan_by_id,
    list_week_plans,
    set_default_week_plan,
    update_week_plan,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/week-plans", tags=["Week Plans"])


@router.get("", response_model=list[WeekPlanListItem])
async def get_week_plans(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[WeekPlanListItem]:
    """List all week plans with day counts."""
    rows = await list_week_plans(db, user.id)

    return [
        WeekPlanListItem(
            id=row["plan"].id,
            name=row["plan"].name,
            is_default=row["plan"].is_default,
            day_count=row["day_count"],
        )
        for row in rows
    ]


@router.get("/{plan_id}", response_model=WeekPlanResponse)
async def get_week_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeekPlanResponse:
    """Get a single week plan by ID with full day mapping details."""
    plan = await get_week_plan_by_id(db, plan_id, user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Week plan not found")

    return _plan_to_response(plan)


@router.post("", response_model=WeekPlanResponse, status_code=201)
async def create_week_plan_endpoint(
    data: WeekPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeekPlanResponse:
    """Create a new week plan with weekday-to-template mappings."""
    plan = await create_week_plan(db, data, user_id=user.id)
    return _plan_to_response(plan)


@router.put("/{plan_id}", response_model=WeekPlanResponse)
async def update_week_plan_endpoint(
    plan_id: UUID,
    data: WeekPlanUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeekPlanResponse:
    """Update an existing week plan. Providing days replaces all day mappings."""
    plan = await get_week_plan_by_id(db, plan_id, user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Week plan not found")

    updated = await update_week_plan(db, plan, data)
    return _plan_to_response(updated)


@router.delete("/{plan_id}", status_code=204)
async def delete_week_plan_endpoint(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete a week plan."""
    plan = await get_week_plan_by_id(db, plan_id, user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Week plan not found")

    await delete_week_plan(db, plan)


@router.post("/{plan_id}/set-default", response_model=WeekPlanResponse)
async def set_default_week_plan_endpoint(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WeekPlanResponse:
    """Set a week plan as the default plan for generating new weeks."""
    plan = await get_week_plan_by_id(db, plan_id, user.id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Week plan not found")

    updated = await set_default_week_plan(db, plan)
    return _plan_to_response(updated)


def _plan_to_response(plan) -> WeekPlanResponse:
    """Convert a WeekPlan ORM object to a response schema."""
    return WeekPlanResponse(
        id=plan.id,
        name=plan.name,
        is_default=plan.is_default,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        days=[
            WeekPlanDayResponse(
                id=day.id,
                weekday=day.weekday,
                weekday_name=WEEKDAY_NAMES.get(day.weekday, "Unknown"),
                day_template=DayTemplateCompact(
                    id=day.day_template.id,
                    name=day.day_template.name,
                ),
            )
            for day in sorted(plan.days, key=lambda d: d.weekday)
        ],
    )
