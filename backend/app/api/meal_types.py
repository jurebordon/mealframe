"""
API routes for meal type endpoints.

Provides CRUD operations for meal types.
Per Tech Spec section 4.5 (Setup/Admin Endpoints).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.meal_type import (
    MealTypeCreate,
    MealTypeResponse,
    MealTypeUpdate,
    MealTypeWithCount,
)
from ..services.meal_types import (
    create_meal_type,
    delete_meal_type,
    get_meal_type_by_id,
    list_meal_types,
    update_meal_type,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meal-types", tags=["Meal Types"])


@router.get("", response_model=list[MealTypeWithCount])
async def get_meal_types(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MealTypeWithCount]:
    """List all meal types with meal counts."""
    rows = await list_meal_types(db, user.id)

    return [
        MealTypeWithCount(
            id=row["meal_type"].id,
            name=row["meal_type"].name,
            description=row["meal_type"].description,
            tags=row["meal_type"].tags or [],
            created_at=row["meal_type"].created_at,
            updated_at=row["meal_type"].updated_at,
            meal_count=row["meal_count"],
        )
        for row in rows
    ]


@router.get("/{meal_type_id}", response_model=MealTypeResponse)
async def get_meal_type(
    meal_type_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    """Get a single meal type by ID."""
    meal_type = await get_meal_type_by_id(db, meal_type_id, user.id)
    if meal_type is None:
        raise HTTPException(status_code=404, detail="Meal type not found")

    return MealTypeResponse(
        id=meal_type.id,
        name=meal_type.name,
        description=meal_type.description,
        tags=meal_type.tags or [],
        created_at=meal_type.created_at,
        updated_at=meal_type.updated_at,
    )


@router.post("", response_model=MealTypeResponse, status_code=201)
async def create_meal_type_endpoint(
    data: MealTypeCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    """Create a new meal type."""
    meal_type = await create_meal_type(db, data, user_id=user.id)

    return MealTypeResponse(
        id=meal_type.id,
        name=meal_type.name,
        description=meal_type.description,
        tags=meal_type.tags or [],
        created_at=meal_type.created_at,
        updated_at=meal_type.updated_at,
    )


@router.put("/{meal_type_id}", response_model=MealTypeResponse)
async def update_meal_type_endpoint(
    meal_type_id: UUID,
    data: MealTypeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealTypeResponse:
    """Update an existing meal type."""
    meal_type = await get_meal_type_by_id(db, meal_type_id, user.id)
    if meal_type is None:
        raise HTTPException(status_code=404, detail="Meal type not found")

    updated = await update_meal_type(db, meal_type, data)

    return MealTypeResponse(
        id=updated.id,
        name=updated.name,
        description=updated.description,
        tags=updated.tags or [],
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/{meal_type_id}", status_code=204)
async def delete_meal_type_endpoint(
    meal_type_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete a meal type. Fails if used by day template slots."""
    meal_type = await get_meal_type_by_id(db, meal_type_id, user.id)
    if meal_type is None:
        raise HTTPException(status_code=404, detail="Meal type not found")

    try:
        await delete_meal_type(db, meal_type)
    except Exception:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete meal type that is used by day template slots",
        )
