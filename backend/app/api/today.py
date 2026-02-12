"""
API routes for daily use endpoints.

These are the primary endpoints for the Today View:
- GET /today - Today's meal plan with completion status
- GET /yesterday - Yesterday's plan for review/catch-up
- POST /today/slots - Add an ad-hoc meal to today
- POST /slots/{slot_id}/complete - Mark slot complete with status
- DELETE /slots/{slot_id}/complete - Undo completion
- DELETE /slots/{slot_id} - Remove an ad-hoc slot

See Tech Spec section 4.3 for full specification.
"""
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.common import ErrorCode
from ..schemas.meal import MealCompact
from ..schemas.meal_type import MealTypeCompact
from ..schemas.today import TodayResponse
from ..schemas.weekly_plan import AddAdhocSlotRequest, CompleteSlotRequest, CompleteSlotResponse, WeeklyPlanSlotWithNext
from ..services.today import (
    get_today_response,
    complete_slot,
    uncomplete_slot,
    get_slot_by_id,
    create_adhoc_slot,
    delete_adhoc_slot,
)

router = APIRouter(prefix="/api/v1", tags=["Daily Use"])


@router.get("/today", response_model=TodayResponse)
async def get_today(db: AsyncSession = Depends(get_db)) -> TodayResponse:
    """
    Get today's meal plan with completion status.

    Returns the current day's meal slots with:
    - Meal details (name, portion, macros)
    - Completion status for each slot
    - is_next indicator for the next meal to complete
    - Stats (completed count, total, streak)

    If no plan exists for today, returns an empty slots list with stats.
    """
    today = date.today()
    return await get_today_response(db, today)


@router.get("/yesterday", response_model=TodayResponse)
async def get_yesterday(db: AsyncSession = Depends(get_db)) -> TodayResponse:
    """
    Get yesterday's meal plan for review/catch-up.

    Same response format as /today but for the previous day.
    Useful for the Yesterday Review modal to catch up on unmarked meals.
    """
    yesterday = date.today() - timedelta(days=1)
    return await get_today_response(db, yesterday)


@router.post(
    "/today/slots",
    response_model=WeeklyPlanSlotWithNext,
    status_code=status.HTTP_201_CREATED,
)
async def add_adhoc_slot(
    request: AddAdhocSlotRequest,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanSlotWithNext:
    """
    Add an ad-hoc meal to today's plan.

    Creates a new slot with is_adhoc=True appended after existing slots.
    The meal's first associated meal type is used (if any).

    Returns 404 if no weekly plan exists for today or the meal doesn't exist.
    """
    today = date.today()
    slot = await create_adhoc_slot(db, today, request.meal_id)

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": "No weekly plan exists for today, or meal not found",
                }
            },
        )

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

    return WeeklyPlanSlotWithNext(
        id=slot.id,
        position=slot.position,
        meal_type=meal_type_compact,
        meal=meal_compact,
        completion_status=slot.completion_status,
        completed_at=slot.completed_at,
        is_next=False,
        is_adhoc=slot.is_adhoc,
    )


@router.post(
    "/slots/{slot_id}/complete",
    response_model=CompleteSlotResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_meal_slot(
    slot_id: UUID,
    request: CompleteSlotRequest,
    db: AsyncSession = Depends(get_db),
) -> CompleteSlotResponse:
    """
    Mark a meal slot as complete with a status.

    Valid statuses:
    - followed: Ate the meal as planned
    - adjusted: Ate something similar or modified
    - skipped: Did not eat this meal
    - replaced: Ate something completely different
    - social: Social occasion (eating out, etc.)

    Returns the updated slot with completion_status and completed_at timestamp.
    """
    slot = await complete_slot(db, slot_id, request.status.value)

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": f"Slot with id {slot_id} not found",
                }
            },
        )

    return CompleteSlotResponse(
        id=slot.id,
        completion_status=slot.completion_status,
        completed_at=slot.completed_at,
    )


@router.delete(
    "/slots/{slot_id}/complete",
    response_model=CompleteSlotResponse,
    status_code=status.HTTP_200_OK,
)
async def uncomplete_meal_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CompleteSlotResponse:
    """
    Undo completion of a meal slot (reset to unmarked).

    Clears the completion_status and completed_at timestamp.
    """
    slot = await uncomplete_slot(db, slot_id)

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": f"Slot with id {slot_id} not found",
                }
            },
        )

    return CompleteSlotResponse(
        id=slot.id,
        completion_status=slot.completion_status,
        completed_at=slot.completed_at,
    )


@router.delete(
    "/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meal_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an ad-hoc meal slot.

    Only ad-hoc slots (is_adhoc=True) can be deleted. Template-generated
    slots return 403 Forbidden.
    """
    result = await delete_adhoc_slot(db, slot_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.NOT_FOUND,
                    "message": f"Slot with id {slot_id} not found",
                }
            },
        )

    if result is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Only ad-hoc slots can be deleted",
                }
            },
        )
