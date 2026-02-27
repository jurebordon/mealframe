"""
Service layer for meal type operations.

Handles CRUD operations for meal types.
Per Tech Spec section 4.5 (Setup/Admin Endpoints).
"""
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal_type import MealType
from app.models.meal_to_meal_type import meal_to_meal_type
from app.schemas.meal_type import MealTypeCreate, MealTypeUpdate

logger = logging.getLogger(__name__)


async def list_meal_types(db: AsyncSession) -> list[dict]:
    """
    List all meal types with their assigned meal counts.

    Returns list of dicts with MealType objects and meal_count.
    """
    # Get meal types with counts via subquery
    count_subq = (
        select(
            meal_to_meal_type.c.meal_type_id,
            func.count(meal_to_meal_type.c.meal_id).label("meal_count"),
        )
        .group_by(meal_to_meal_type.c.meal_type_id)
        .subquery()
    )

    result = await db.execute(
        select(MealType, func.coalesce(count_subq.c.meal_count, 0).label("meal_count"))
        .outerjoin(count_subq, MealType.id == count_subq.c.meal_type_id)
        .order_by(MealType.name)
    )
    rows = result.all()

    return [{"meal_type": row[0], "meal_count": row[1]} for row in rows]


async def get_meal_type_by_id(db: AsyncSession, meal_type_id: UUID) -> MealType | None:
    """Get a single meal type by ID."""
    result = await db.execute(
        select(MealType).where(MealType.id == meal_type_id)
    )
    return result.scalars().first()


async def create_meal_type(db: AsyncSession, data: MealTypeCreate, user_id: Optional[UUID] = None) -> MealType:
    """Create a new meal type."""
    mt_kwargs = dict(
        name=data.name,
        description=data.description,
        tags=data.tags,
    )
    if user_id:
        mt_kwargs["user_id"] = user_id
    meal_type = MealType(**mt_kwargs)
    db.add(meal_type)
    await db.flush()
    return meal_type


async def update_meal_type(db: AsyncSession, meal_type: MealType, data: MealTypeUpdate) -> MealType:
    """Update an existing meal type. Only non-None fields are updated."""
    if data.name is not None:
        meal_type.name = data.name
    if data.description is not None:
        meal_type.description = data.description
    if data.tags is not None:
        meal_type.tags = data.tags

    await db.flush()
    await db.refresh(meal_type)
    return meal_type


async def delete_meal_type(db: AsyncSession, meal_type: MealType) -> None:
    """Delete a meal type. Will fail if meal type is used by day template slots (RESTRICT)."""
    await db.delete(meal_type)
    await db.flush()
