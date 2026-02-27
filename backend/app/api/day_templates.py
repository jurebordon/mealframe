"""
API routes for day template endpoints.

Provides full CRUD operations for day templates.
Per Tech Spec section 4.5 (Setup/Admin Endpoints).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import ADMIN_USER_ID, get_optional_user
from ..models.user import User
from ..schemas.day_template import (
    DayTemplateCreate,
    DayTemplateListItem,
    DayTemplateResponse,
    DayTemplateSlotResponse,
    DayTemplateUpdate,
)
from ..schemas.meal_type import MealTypeCompact
from ..services.day_templates import (
    create_day_template,
    delete_day_template,
    get_day_template_by_id,
    list_day_templates,
    update_day_template,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/day-templates", tags=["Day Templates"])


@router.get("", response_model=list[DayTemplateListItem])
async def get_day_templates(
    db: AsyncSession = Depends(get_db),
) -> list[DayTemplateListItem]:
    """
    List all day templates with slot counts and previews.

    Returns templates ordered by name, each with:
    - slot_count: Number of meal slots
    - slot_preview: Arrow-separated meal type names (e.g., "Breakfast → Lunch → Dinner")
    """
    rows = await list_day_templates(db)

    return [
        DayTemplateListItem(
            id=row["template"].id,
            name=row["template"].name,
            notes=row["template"].notes,
            max_calories_kcal=row["template"].max_calories_kcal,
            max_protein_g=row["template"].max_protein_g,
            slot_count=row["slot_count"],
            slot_preview=row["slot_preview"],
        )
        for row in rows
    ]


@router.get("/{template_id}", response_model=DayTemplateResponse)
async def get_day_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DayTemplateResponse:
    """Get a single day template by ID with full slot details."""
    template = await get_day_template_by_id(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Day template not found")

    return _template_to_response(template)


@router.post("", response_model=DayTemplateResponse, status_code=201)
async def create_day_template_endpoint(
    data: DayTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> DayTemplateResponse:
    """Create a new day template with ordered meal type slots."""
    user_id = user.id if user else ADMIN_USER_ID
    template = await create_day_template(db, data, user_id=user_id)
    return _template_to_response(template)


@router.put("/{template_id}", response_model=DayTemplateResponse)
async def update_day_template_endpoint(
    template_id: UUID,
    data: DayTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> DayTemplateResponse:
    """Update an existing day template. Providing slots replaces all existing slots."""
    template = await get_day_template_by_id(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Day template not found")

    updated = await update_day_template(db, template, data)
    return _template_to_response(updated)


@router.delete("/{template_id}", status_code=204)
async def delete_day_template_endpoint(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a day template. Fails if used by week plans."""
    template = await get_day_template_by_id(db, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Day template not found")

    try:
        await delete_day_template(db, template)
    except Exception:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete day template that is used by week plans",
        )


def _template_to_response(template) -> DayTemplateResponse:
    """Convert a DayTemplate ORM object to a response schema."""
    return DayTemplateResponse(
        id=template.id,
        name=template.name,
        notes=template.notes,
        max_calories_kcal=template.max_calories_kcal,
        max_protein_g=template.max_protein_g,
        created_at=template.created_at,
        updated_at=template.updated_at,
        slots=[
            DayTemplateSlotResponse(
                id=slot.id,
                position=slot.position,
                meal_type=MealTypeCompact(
                    id=slot.meal_type.id,
                    name=slot.meal_type.name,
                ),
            )
            for slot in sorted(template.slots, key=lambda s: s.position)
        ],
    )
