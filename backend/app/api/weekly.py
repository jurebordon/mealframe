"""
API routes for weekly planning endpoints.

These are the endpoints for week generation and management:
- GET /weekly-plans/current - Current week's plan
- POST /weekly-plans/generate - Generate a new week
- PUT /weekly-plans/current/days/{date}/template - Switch day template
- PUT /weekly-plans/current/days/{date}/override - Mark day as "no plan"
- DELETE /weekly-plans/current/days/{date}/override - Remove override

See Tech Spec section 4.4 for full specification.
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import ADMIN_USER_ID, get_optional_user
from ..models.user import User
from ..schemas.common import ErrorCode, WEEKDAY_NAMES
from ..schemas.weekly_plan import (
    WeeklyPlanInstanceResponse,
    WeeklyPlanInstanceDayResponse,
    WeeklyPlanGenerateRequest,
    SwitchTemplateRequest,
    SetOverrideRequest,
    OverrideResponse,
    WeeklyPlanSlotResponse,
    CompletionSummary,
)
from ..schemas.day_template import DayTemplateCompact
from ..schemas.week_plan import WeekPlanCompact
from ..schemas.meal import MealCompact
from ..schemas.meal_type import MealTypeCompact
from ..services.weekly import (
    generate_weekly_plan,
    regenerate_weekly_plan,
    get_current_week_instance,
    get_week_instance,
    get_full_weekly_instance,
    get_instance_day,
    get_slots_for_instance_day,
    switch_day_template,
    set_day_override,
    clear_day_override,
    is_date_in_week,
)

router = APIRouter(prefix="/api/v1/weekly-plans", tags=["Weekly Planning"])


def build_slot_response(slot) -> WeeklyPlanSlotResponse:
    """Build a slot response from ORM object."""
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

    meal_type_compact = None
    if slot.meal_type:
        meal_type_compact = MealTypeCompact(
            id=slot.meal_type.id,
            name=slot.meal_type.name,
        )

    actual_meal_compact = None
    if hasattr(slot, 'actual_meal') and slot.actual_meal:
        actual_meal_compact = MealCompact(
            id=slot.actual_meal.id,
            name=slot.actual_meal.name,
            portion_description=slot.actual_meal.portion_description,
            calories_kcal=slot.actual_meal.calories_kcal,
            protein_g=slot.actual_meal.protein_g,
            carbs_g=slot.actual_meal.carbs_g,
            sugar_g=slot.actual_meal.sugar_g,
            fat_g=slot.actual_meal.fat_g,
            saturated_fat_g=slot.actual_meal.saturated_fat_g,
            fiber_g=slot.actual_meal.fiber_g,
        )

    return WeeklyPlanSlotResponse(
        id=slot.id,
        position=slot.position,
        meal_type=meal_type_compact,
        meal=meal_compact,
        completion_status=slot.completion_status,
        completed_at=slot.completed_at,
        is_adhoc=slot.is_adhoc,
        is_manual_override=slot.is_manual_override,
        actual_meal=actual_meal_compact,
    )


async def build_day_response(
    db: AsyncSession, instance_id: UUID, instance_day
) -> WeeklyPlanInstanceDayResponse:
    """Build a day response with slots."""
    slots = await get_slots_for_instance_day(db, instance_id, instance_day.date)

    template_compact = None
    if instance_day.day_template:
        template_compact = DayTemplateCompact(
            id=instance_day.day_template.id,
            name=instance_day.day_template.name,
        )

    completed_count = sum(1 for s in slots if s.completion_status is not None)

    return WeeklyPlanInstanceDayResponse(
        date=instance_day.date,
        weekday=WEEKDAY_NAMES.get(instance_day.date.weekday(), "Unknown"),
        template=template_compact,
        is_override=instance_day.is_override,
        override_reason=instance_day.override_reason,
        slots=[build_slot_response(s) for s in slots],
        completion_summary=CompletionSummary(
            completed=completed_count,
            total=len(slots),
        ),
    )


async def build_instance_response(
    db: AsyncSession, instance
) -> WeeklyPlanInstanceResponse:
    """Build a full instance response with all days and slots."""
    # Get full instance with relations
    full_instance = await get_full_weekly_instance(db, instance.id)

    week_plan_compact = None
    if full_instance.week_plan:
        week_plan_compact = WeekPlanCompact(
            id=full_instance.week_plan.id,
            name=full_instance.week_plan.name,
        )

    # Build day responses
    days = []
    for instance_day in sorted(full_instance.days, key=lambda d: d.date):
        day_response = await build_day_response(db, instance.id, instance_day)
        days.append(day_response)

    return WeeklyPlanInstanceResponse(
        id=full_instance.id,
        week_start_date=full_instance.week_start_date,
        week_plan=week_plan_compact,
        days=days,
    )


@router.get("/current", response_model=WeeklyPlanInstanceResponse)
async def get_current_week(
    week_start_date: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanInstanceResponse:
    """
    Get a week's plan.

    Returns the weekly plan instance for the specified week with all days and slots.
    Each day includes:
    - Template information
    - Slots with meal assignments
    - Completion summary

    Query parameters:
    - week_start_date (optional): Monday of the target week. Defaults to current week.

    If no plan exists for the specified week, returns 404.
    """
    instance = await get_week_instance(db, week_start_date)

    if not instance:
        week_desc = f"week starting {week_start_date}" if week_start_date else "the current week"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": f"No plan exists for {week_desc}",
                }
            },
        )

    return await build_instance_response(db, instance)


@router.post(
    "/generate",
    response_model=WeeklyPlanInstanceResponse,
    responses={
        201: {"description": "New week created"},
        200: {"description": "Existing week regenerated (uncompleted slots refreshed)"},
    },
)
async def generate_week(
    request: WeeklyPlanGenerateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> WeeklyPlanInstanceResponse:
    """
    Generate or regenerate a weekly plan.

    If no plan exists for the target week:
    - Creates a new weekly plan instance using the default week plan
    - For each day, assigns meals via round-robin rotation
    - Returns 201 Created

    If a plan already exists (smart regeneration):
    - Only regenerates slots that have no completion status
    - Preserves all completed slots and their meal assignments
    - Useful for refreshing meal assignments without losing progress
    - Returns 200 OK

    Request body:
    - week_start_date (optional): Monday of the target week. Defaults to next Monday.

    Returns the generated/regenerated weekly plan with all days and slots.

    Errors:
    - 400 Bad Request: No default week plan, or invalid date
    """
    user_id = user.id if user else ADMIN_USER_ID
    try:
        instance = await generate_weekly_plan(
            db,
            week_start_date=request.week_start_date,
            user_id=user_id,
        )
        response.status_code = status.HTTP_201_CREATED
        return await build_instance_response(db, instance)

    except ValueError as e:
        error_message = str(e)

        # If week already exists, try smart regeneration
        if "already exists" in error_message:
            try:
                instance = await regenerate_weekly_plan(
                    db,
                    week_start_date=request.week_start_date,
                )
                # Return 200 OK for regeneration (not 201 Created)
                response.status_code = status.HTTP_200_OK
                return await build_instance_response(db, instance)
            except ValueError as regen_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": {
                            "code": ErrorCode.VALIDATION_ERROR,
                            "message": str(regen_error),
                        }
                    },
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": ErrorCode.VALIDATION_ERROR,
                        "message": error_message,
                    }
                },
            )


@router.put(
    "/current/days/{target_date}/template",
    response_model=WeeklyPlanInstanceDayResponse,
)
async def switch_template(
    target_date: date = Path(..., description="The date to switch (YYYY-MM-DD)"),
    request: SwitchTemplateRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanInstanceDayResponse:
    """
    Switch a day's template.

    Deletes existing slots and regenerates them using the new template.
    New meals are assigned via round-robin rotation.

    Note: Completion statuses are lost when switching templates.

    Path parameters:
    - target_date: The date to modify (must be in current week)

    Request body:
    - day_template_id: UUID of the new template

    Returns the updated day with regenerated slots.
    """
    instance = await get_current_week_instance(db)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": "No plan exists for the current week",
                }
            },
        )

    # Verify date is in current week
    if not is_date_in_week(target_date, instance.week_start_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": f"Date {target_date} is not in the current week",
                }
            },
        )

    try:
        instance_day = await switch_day_template(
            db,
            instance_id=instance.id,
            target_date=target_date,
            new_template_id=request.day_template_id,
        )
        return await build_day_response(db, instance.id, instance_day)

    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": ErrorCode.NOT_FOUND,
                        "message": error_message,
                    }
                },
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": error_message,
                }
            },
        )


@router.put(
    "/current/days/{target_date}/override",
    response_model=OverrideResponse,
)
async def set_override(
    target_date: date = Path(..., description="The date to override (YYYY-MM-DD)"),
    request: SetOverrideRequest = ...,
    db: AsyncSession = Depends(get_db),
) -> OverrideResponse:
    """
    Mark a day as "no plan" override.

    Deletes all slots for the day and marks it as an override.
    Use this for exceptional days (e.g., vacation, events).

    Path parameters:
    - target_date: The date to override (must be in current week)

    Request body:
    - reason (optional): Reason for the override (e.g., "LAN party")

    Returns the override status.
    """
    instance = await get_current_week_instance(db)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": "No plan exists for the current week",
                }
            },
        )

    # Verify date is in current week
    if not is_date_in_week(target_date, instance.week_start_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": f"Date {target_date} is not in the current week",
                }
            },
        )

    try:
        instance_day = await set_day_override(
            db,
            instance_id=instance.id,
            target_date=target_date,
            reason=request.reason,
        )
        return OverrideResponse(
            date=instance_day.date,
            is_override=instance_day.is_override,
            override_reason=instance_day.override_reason,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": str(e),
                }
            },
        )


@router.delete(
    "/current/days/{target_date}/override",
    response_model=WeeklyPlanInstanceDayResponse,
)
async def clear_override(
    target_date: date = Path(..., description="The date to restore (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanInstanceDayResponse:
    """
    Remove override and restore plan for a day.

    Clears the override flag and regenerates slots using the day's template.
    New meals are assigned via round-robin rotation.

    Path parameters:
    - target_date: The date to restore (must be in current week)

    Returns the day with restored slots.
    """
    instance = await get_current_week_instance(db)

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": "No plan exists for the current week",
                }
            },
        )

    # Verify date is in current week
    if not is_date_in_week(target_date, instance.week_start_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": f"Date {target_date} is not in the current week",
                }
            },
        )

    try:
        instance_day = await clear_day_override(
            db,
            instance_id=instance.id,
            target_date=target_date,
        )
        return await build_day_response(db, instance.id, instance_day)

    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": ErrorCode.NOT_FOUND,
                        "message": error_message,
                    }
                },
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": error_message,
                }
            },
        )
