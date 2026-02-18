"""
Service layer for day template operations.

Handles CRUD operations for day templates and their slots.
Per Tech Spec section 4.5 (Setup/Admin Endpoints).
"""
import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.day_template import DayTemplate, DayTemplateSlot
from app.models.meal_type import MealType
from app.schemas.day_template import DayTemplateCreate, DayTemplateSlotCreate, DayTemplateUpdate

logger = logging.getLogger(__name__)


async def list_day_templates(db: AsyncSession) -> list[dict]:
    """
    List all day templates with slot counts and previews.

    Returns list of dicts with template info, slot_count, and slot_preview.
    """
    result = await db.execute(
        select(DayTemplate).order_by(DayTemplate.name)
    )
    templates = result.scalars().all()

    items = []
    for template in templates:
        # Get meal type names ordered by slot position
        mt_result = await db.execute(
            select(MealType.name)
            .join(DayTemplateSlot, DayTemplateSlot.meal_type_id == MealType.id)
            .where(DayTemplateSlot.day_template_id == template.id)
            .order_by(DayTemplateSlot.position)
        )
        meal_type_names = [row[0] for row in mt_result.all()]

        items.append({
            "template": template,
            "slot_count": len(meal_type_names),
            "slot_preview": " → ".join(meal_type_names) if meal_type_names else None,
        })

    return items


async def get_day_template_by_id(db: AsyncSession, template_id: UUID) -> DayTemplate | None:
    """Get a single day template by ID with slots eagerly loaded."""
    result = await db.execute(
        select(DayTemplate)
        .options(selectinload(DayTemplate.slots).selectinload(DayTemplateSlot.meal_type))
        .where(DayTemplate.id == template_id)
    )
    return result.scalars().first()


async def create_day_template(db: AsyncSession, data: DayTemplateCreate) -> DayTemplate:
    """Create a new day template with slots."""
    template = DayTemplate(
        name=data.name,
        notes=data.notes,
        max_calories_kcal=data.max_calories_kcal,
        max_protein_g=data.max_protein_g,
    )
    db.add(template)
    await db.flush()

    # Create slots
    await _replace_slots(db, template.id, data.slots)

    # Reload with relationships
    return await get_day_template_by_id(db, template.id)


async def update_day_template(
    db: AsyncSession, template: DayTemplate, data: DayTemplateUpdate
) -> DayTemplate:
    """Update an existing day template. Only non-None fields are updated."""
    if data.name is not None:
        template.name = data.name
    if data.notes is not None:
        template.notes = data.notes
    if "max_calories_kcal" in data.model_fields_set:
        template.max_calories_kcal = data.max_calories_kcal
    if "max_protein_g" in data.model_fields_set:
        template.max_protein_g = data.max_protein_g

    # Replace slots if provided
    if data.slots is not None:
        await _replace_slots(db, template.id, data.slots)

    await db.flush()

    # Capture ID before expunging (async SQLAlchemy can't lazy-load after expire)
    template_id = template.id
    db.expunge(template)

    # Reload with fresh relationships
    return await get_day_template_by_id(db, template_id)


async def delete_day_template(db: AsyncSession, template: DayTemplate) -> None:
    """Delete a day template. Will fail if used by week plan days (RESTRICT)."""
    await db.delete(template)
    await db.flush()


async def _replace_slots(
    db: AsyncSession,
    template_id: UUID,
    slots: list[DayTemplateSlotCreate],
) -> None:
    """Delete existing slots and create new ones for a template."""
    # Delete existing slots
    await db.execute(
        delete(DayTemplateSlot).where(DayTemplateSlot.day_template_id == template_id)
    )

    # Create new slots
    for slot_data in slots:
        slot = DayTemplateSlot(
            day_template_id=template_id,
            position=slot_data.position,
            meal_type_id=slot_data.meal_type_id,
        )
        db.add(slot)

    await db.flush()
