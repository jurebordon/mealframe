"""
API routes for meal endpoints.

Provides CRUD operations and CSV import for meals.
Per Tech Spec section 4.5 (CRUD) and frozen spec MEAL_IMPORT_GUIDE.md (import).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.meal import (
    MealCreate,
    MealImportResult,
    MealListItem,
    MealResponse,
    MealUpdate,
)
from ..schemas.common import PaginatedResponse
from ..services.meals import (
    create_meal,
    delete_meal,
    get_meal_by_id,
    import_meals_from_csv,
    list_meals,
    update_meal,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meals", tags=["Meals"])


@router.get("", response_model=PaginatedResponse[MealListItem])
async def get_meals(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search by meal name"),
    meal_type_id: UUID | None = Query(default=None, description="Filter by meal type ID"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaginatedResponse[MealListItem]:
    """List all meals with pagination, optional search and meal type filter."""
    meals, total = await list_meals(
        db, user_id=user.id, page=page, page_size=page_size, search=search, meal_type_id=meal_type_id
    )

    items = [
        MealListItem(
            id=m.id,
            name=m.name,
            portion_description=m.portion_description,
            calories_kcal=m.calories_kcal,
            protein_g=m.protein_g,
            carbs_g=m.carbs_g,
            sugar_g=m.sugar_g,
            fat_g=m.fat_g,
            saturated_fat_g=m.saturated_fat_g,
            fiber_g=m.fiber_g,
            meal_types=[{"id": mt.id, "name": mt.name} for mt in m.meal_types],
        )
        for m in meals
    ]

    return PaginatedResponse.create(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal(
    meal_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealResponse:
    """Get a single meal by ID."""
    meal = await get_meal_by_id(db, meal_id, user.id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")

    return MealResponse(
        id=meal.id,
        name=meal.name,
        portion_description=meal.portion_description,
        calories_kcal=meal.calories_kcal,
        protein_g=meal.protein_g,
        carbs_g=meal.carbs_g,
        fat_g=meal.fat_g,
        notes=meal.notes,
        created_at=meal.created_at,
        updated_at=meal.updated_at,
        meal_types=[{"id": mt.id, "name": mt.name} for mt in meal.meal_types],
    )


@router.post("", response_model=MealResponse, status_code=201)
async def create_meal_endpoint(
    data: MealCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealResponse:
    """Create a new meal."""
    meal = await create_meal(db, data, user_id=user.id)

    return MealResponse(
        id=meal.id,
        name=meal.name,
        portion_description=meal.portion_description,
        calories_kcal=meal.calories_kcal,
        protein_g=meal.protein_g,
        carbs_g=meal.carbs_g,
        fat_g=meal.fat_g,
        notes=meal.notes,
        created_at=meal.created_at,
        updated_at=meal.updated_at,
        meal_types=[{"id": mt.id, "name": mt.name} for mt in meal.meal_types],
    )


@router.put("/{meal_id}", response_model=MealResponse)
async def update_meal_endpoint(
    meal_id: UUID,
    data: MealUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealResponse:
    """Update an existing meal."""
    meal = await get_meal_by_id(db, meal_id, user.id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")

    updated = await update_meal(db, meal, data)

    return MealResponse(
        id=updated.id,
        name=updated.name,
        portion_description=updated.portion_description,
        calories_kcal=updated.calories_kcal,
        protein_g=updated.protein_g,
        carbs_g=updated.carbs_g,
        fat_g=updated.fat_g,
        notes=updated.notes,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        meal_types=[{"id": mt.id, "name": mt.name} for mt in updated.meal_types],
    )


@router.delete("/{meal_id}", status_code=204)
async def delete_meal_endpoint(
    meal_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete a meal."""
    meal = await get_meal_by_id(db, meal_id, user.id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")

    await delete_meal(db, meal)


@router.post("/import", response_model=MealImportResult)
async def import_meals(
    file: UploadFile = File(..., description="CSV file to import"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MealImportResult:
    """
    Import meals from a CSV file.

    Accepts multipart/form-data with a CSV file. Per MEAL_IMPORT_GUIDE.md:
    - Required columns: name, portion_description
    - Optional columns: calories_kcal, protein_g, carbs_g, fat_g, meal_types, notes
    - Rows with errors are skipped, others are imported
    - Unknown meal types generate warnings but don't block meal creation
    """
    # Validate file type
    if file.content_type and file.content_type not in (
        "text/csv",
        "text/plain",
        "application/vnd.ms-excel",
        "application/octet-stream",
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Expected CSV file.",
        )

    # Read file content
    try:
        raw_bytes = await file.read()
        csv_content = raw_bytes.decode("utf-8-sig")  # Handle BOM from Excel
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding error. Please save the file as UTF-8.",
        )

    if not csv_content.strip():
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty.",
        )

    result = await import_meals_from_csv(db, csv_content, user_id=user.id)
    return result
