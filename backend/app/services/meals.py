"""
Service layer for meal operations.

Handles CRUD operations and CSV parsing/import with meal-type associations.
Per frozen spec: MEAL_IMPORT_GUIDE.md (for import) and TECH_SPEC_v0.md section 4.5 (for CRUD).
"""
import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal import Meal
from app.models.meal_type import MealType
from app.models.meal_to_meal_type import meal_to_meal_type
from app.schemas.meal import (
    MealCreate,
    MealImportError,
    MealImportResult,
    MealImportSummary,
    MealImportWarning,
    MealUpdate,
)

logger = logging.getLogger(__name__)

# Expected CSV columns per MEAL_IMPORT_GUIDE.md
REQUIRED_COLUMNS = {"name", "portion_description"}
OPTIONAL_COLUMNS = {"calories_kcal", "protein_g", "carbs_g", "sugar_g", "fat_g", "saturated_fat_g", "fiber_g", "meal_types", "notes"}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


async def _resolve_meal_types(
    db: AsyncSession,
) -> dict[str, MealType]:
    """Build a lookup dict of meal type name -> MealType object (case-sensitive)."""
    result = await db.execute(select(MealType))
    meal_types = result.scalars().all()
    return {mt.name: mt for mt in meal_types}


def _parse_optional_int(value: str, field_name: str) -> tuple[int | None, str | None]:
    """Parse an optional integer field. Returns (value, warning_message)."""
    if not value or not value.strip():
        return None, None
    try:
        return int(value.strip()), None
    except (ValueError, TypeError):
        return None, f"Invalid {field_name} value '{value}', imported with null value"


def _parse_optional_decimal(value: str, field_name: str) -> tuple[Decimal | None, str | None]:
    """Parse an optional decimal field. Returns (value, warning_message)."""
    if not value or not value.strip():
        return None, None
    try:
        return Decimal(value.strip()), None
    except (InvalidOperation, ValueError, TypeError):
        return None, f"Invalid {field_name} value '{value}', imported with null value"


async def import_meals_from_csv(
    db: AsyncSession,
    csv_content: str,
) -> MealImportResult:
    """
    Import meals from CSV content.

    Per MEAL_IMPORT_GUIDE.md:
    - Rows with errors (missing required fields) are skipped, others are imported
    - Duplicate names are allowed (creates new meal)
    - Unknown meal types are logged as warnings, meal is still created
    - Missing optional fields result in null values

    Args:
        db: Database session
        csv_content: Raw CSV string content (UTF-8)

    Returns:
        MealImportResult with summary, warnings, and errors
    """
    warnings: list[MealImportWarning] = []
    errors: list[MealImportError] = []
    created_count = 0

    # Resolve all meal types upfront
    meal_type_lookup = await _resolve_meal_types(db)

    # Parse CSV
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
    except Exception as e:
        return MealImportResult(
            success=False,
            summary=MealImportSummary(total_rows=0, created=0, skipped=0, warnings=0),
            errors=[MealImportError(row=0, message=f"Failed to parse CSV: {e}")],
        )

    # Validate header
    if reader.fieldnames is None:
        return MealImportResult(
            success=False,
            summary=MealImportSummary(total_rows=0, created=0, skipped=0, warnings=0),
            errors=[MealImportError(row=0, message="CSV file is empty or has no header row")],
        )

    # Check required columns exist
    header_set = {f.strip() for f in reader.fieldnames if f}
    missing_required = REQUIRED_COLUMNS - header_set
    if missing_required:
        return MealImportResult(
            success=False,
            summary=MealImportSummary(total_rows=0, created=0, skipped=0, warnings=0),
            errors=[MealImportError(
                row=0,
                message=f"Missing required columns: {', '.join(sorted(missing_required))}",
            )],
        )

    rows = list(reader)
    total_rows = len(rows)

    # Filter out completely empty rows (trailing blank rows)
    rows = [row for row in rows if any(v.strip() for v in row.values() if v)]

    for row_idx, row in enumerate(rows):
        row_num = row_idx + 1  # 1-based row number (excluding header)

        # Strip whitespace from all values
        row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}

        # Validate required fields
        name = row.get("name", "").strip()
        portion_description = row.get("portion_description", "").strip()

        if not name:
            errors.append(MealImportError(
                row=row_num,
                message="Missing required field: name",
            ))
            continue

        if not portion_description:
            errors.append(MealImportError(
                row=row_num,
                message="Missing required field: portion_description",
            ))
            continue

        # Parse optional numeric fields
        row_warnings: list[str] = []

        calories_kcal, cal_warn = _parse_optional_int(row.get("calories_kcal", ""), "calories_kcal")
        if cal_warn:
            row_warnings.append(cal_warn)

        protein_g, pro_warn = _parse_optional_decimal(row.get("protein_g", ""), "protein_g")
        if pro_warn:
            row_warnings.append(pro_warn)

        carbs_g, carb_warn = _parse_optional_decimal(row.get("carbs_g", ""), "carbs_g")
        if carb_warn:
            row_warnings.append(carb_warn)

        sugar_g, sugar_warn = _parse_optional_decimal(row.get("sugar_g", ""), "sugar_g")
        if sugar_warn:
            row_warnings.append(sugar_warn)

        fat_g, fat_warn = _parse_optional_decimal(row.get("fat_g", ""), "fat_g")
        if fat_warn:
            row_warnings.append(fat_warn)

        saturated_fat_g, sat_fat_warn = _parse_optional_decimal(row.get("saturated_fat_g", ""), "saturated_fat_g")
        if sat_fat_warn:
            row_warnings.append(sat_fat_warn)

        fiber_g, fiber_warn = _parse_optional_decimal(row.get("fiber_g", ""), "fiber_g")
        if fiber_warn:
            row_warnings.append(fiber_warn)

        notes = row.get("notes", "").strip() or None

        # Create meal
        meal = Meal(
            name=name,
            portion_description=portion_description,
            calories_kcal=calories_kcal,
            protein_g=protein_g,
            carbs_g=carbs_g,
            sugar_g=sugar_g,
            fat_g=fat_g,
            saturated_fat_g=saturated_fat_g,
            fiber_g=fiber_g,
            notes=notes,
        )
        db.add(meal)
        await db.flush()  # Get the meal ID

        # Handle meal type associations
        meal_types_str = row.get("meal_types", "").strip()
        if meal_types_str:
            type_names = [t.strip() for t in meal_types_str.split(",") if t.strip()]
            for type_name in type_names:
                mt = meal_type_lookup.get(type_name)
                if mt is None:
                    row_warnings.append(
                        f"Meal type '{type_name}' not found, skipping assignment"
                    )
                else:
                    await db.execute(
                        meal_to_meal_type.insert().values(
                            meal_id=meal.id,
                            meal_type_id=mt.id,
                        )
                    )
            await db.flush()

        # Add any warnings from this row
        for warn_msg in row_warnings:
            warnings.append(MealImportWarning(row=row_num, message=warn_msg))

        created_count += 1

    # Update total_rows to reflect non-empty rows
    total_rows = len(rows)

    return MealImportResult(
        success=True,
        summary=MealImportSummary(
            total_rows=total_rows,
            created=created_count,
            skipped=total_rows - created_count,
            warnings=len(warnings),
        ),
        warnings=warnings,
        errors=errors,
    )


# =============================================================================
# CRUD Operations
# =============================================================================


async def list_meals(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    meal_type_id: UUID | None = None,
) -> tuple[list[Meal], int]:
    """
    List meals with pagination, optional name search, and meal type filter.

    Returns (meals, total_count) tuple.
    """
    # Base query with eager-loaded meal_types
    query = select(Meal).options(selectinload(Meal.meal_types))
    count_query = select(func.count(Meal.id))

    # Search filter (name only, case-insensitive)
    if search:
        query = query.where(Meal.name.ilike(f"%{search}%"))
        count_query = count_query.where(Meal.name.ilike(f"%{search}%"))

    # Meal type filter
    if meal_type_id:
        query = query.join(meal_to_meal_type).where(
            meal_to_meal_type.c.meal_type_id == meal_type_id
        )
        count_query = count_query.join(meal_to_meal_type).where(
            meal_to_meal_type.c.meal_type_id == meal_type_id
        )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    offset = (page - 1) * page_size
    query = query.order_by(Meal.name.asc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    meals = list(result.scalars().unique().all())

    return meals, total


async def get_meal_by_id(db: AsyncSession, meal_id: UUID) -> Meal | None:
    """Get a single meal by ID with meal_types eagerly loaded."""
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.meal_types))
        .where(Meal.id == meal_id)
    )
    return result.scalars().first()


async def create_meal(db: AsyncSession, data: MealCreate) -> Meal:
    """Create a new meal with optional meal type associations."""
    meal = Meal(
        name=data.name,
        portion_description=data.portion_description,
        calories_kcal=data.calories_kcal,
        protein_g=data.protein_g,
        carbs_g=data.carbs_g,
        sugar_g=data.sugar_g,
        fat_g=data.fat_g,
        saturated_fat_g=data.saturated_fat_g,
        fiber_g=data.fiber_g,
        notes=data.notes,
    )
    db.add(meal)
    await db.flush()

    # Set meal type associations
    if data.meal_type_ids:
        for mt_id in data.meal_type_ids:
            await db.execute(
                meal_to_meal_type.insert().values(
                    meal_id=meal.id,
                    meal_type_id=mt_id,
                )
            )
        await db.flush()

    # Reload with relationships
    await db.refresh(meal)
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.meal_types))
        .where(Meal.id == meal.id)
    )
    return result.scalars().first()


async def update_meal(db: AsyncSession, meal: Meal, data: MealUpdate) -> Meal:
    """Update an existing meal. Only non-None fields are updated."""
    # Update scalar fields
    if data.name is not None:
        meal.name = data.name
    if data.portion_description is not None:
        meal.portion_description = data.portion_description
    if data.calories_kcal is not None:
        meal.calories_kcal = data.calories_kcal
    if data.protein_g is not None:
        meal.protein_g = data.protein_g
    if data.carbs_g is not None:
        meal.carbs_g = data.carbs_g
    if data.sugar_g is not None:
        meal.sugar_g = data.sugar_g
    if data.fat_g is not None:
        meal.fat_g = data.fat_g
    if data.saturated_fat_g is not None:
        meal.saturated_fat_g = data.saturated_fat_g
    if data.fiber_g is not None:
        meal.fiber_g = data.fiber_g
    if data.notes is not None:
        meal.notes = data.notes

    # Replace meal type associations if provided
    if data.meal_type_ids is not None:
        await db.execute(
            delete(meal_to_meal_type).where(
                meal_to_meal_type.c.meal_id == meal.id
            )
        )
        for mt_id in data.meal_type_ids:
            await db.execute(
                meal_to_meal_type.insert().values(
                    meal_id=meal.id,
                    meal_type_id=mt_id,
                )
            )

    await db.flush()

    # Expire cached relationships and reload
    db.expire(meal, ["meal_types"])
    result = await db.execute(
        select(Meal)
        .options(selectinload(Meal.meal_types))
        .where(Meal.id == meal.id)
    )
    return result.scalars().first()


async def delete_meal(db: AsyncSession, meal: Meal) -> None:
    """Delete a meal. Cascades to meal_to_meal_type junction table."""
    await db.delete(meal)
    await db.flush()
