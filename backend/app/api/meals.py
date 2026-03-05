"""
API routes for meal endpoints.

Provides CRUD operations and CSV import for meals.
Per Tech Spec section 4.5 (CRUD) and frozen spec MEAL_IMPORT_GUIDE.md (import).
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.meal import (
    AICaptureResponse,
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
from ..services.ai_capture import (
    analyze_food_image,
    AICaptureFailed,
    AITimeoutError,
    FoodNotDetected,
)
from ..services.image_storage import validate_image_content_type
from ..services.meal_types import list_meal_types

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/meals", tags=["Meals"])


@router.get("", response_model=PaginatedResponse[MealListItem])
async def get_meals(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(default=None, description="Search by meal name"),
    meal_type_id: UUID | None = Query(default=None, description="Filter by meal type ID"),
    source: str | None = Query(default=None, description="Filter by source: 'manual' or 'ai_capture'"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaginatedResponse[MealListItem]:
    """List all meals with pagination, optional search, meal type, and source filter."""
    meals, total = await list_meals(
        db, user_id=user.id, page=page, page_size=page_size, search=search, meal_type_id=meal_type_id, source=source
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
            source=m.source,
            meal_types=[{"id": mt.id, "name": mt.name} for mt in m.meal_types],
        )
        for m in meals
    ]

    return PaginatedResponse.create(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("/ai-capture", response_model=AICaptureResponse)
async def ai_capture_meal(
    image: UploadFile = File(..., description="Food photo (JPEG or PNG, max 10MB)"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AICaptureResponse:
    """
    Analyze a food photo using GPT-4o vision and return estimated meal data.

    This endpoint analyzes but does NOT save. On confirmation, the frontend
    calls POST /meals to create the meal record.

    Returns structured meal data: name, portion description, macros, confidence score.
    """
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

    # Validate content type
    if not validate_image_content_type(image.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {image.content_type}. Expected JPEG or PNG.",
        )

    # Read and size-check
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image too large. Maximum size is 10MB.",
        )

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    # Fetch user's meal type names for the vision prompt
    meal_type_rows = await list_meal_types(db, user_id=user.id)
    meal_type_names = [row["meal_type"].name for row in meal_type_rows]

    try:
        analysis = await analyze_food_image(
            image_bytes,
            user_id=user.id,
            db=db,
            captured_at=datetime.now(timezone.utc),
            meal_type_names=meal_type_names or None,
        )
    except FoodNotDetected as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AITimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Analysis took too long. Please try again.",
        )
    except AICaptureFailed as e:
        logger.error("AI capture failed for user %s: %s", user.id, e)
        raise HTTPException(
            status_code=502,
            detail="Could not analyze image. Please try again.",
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return AICaptureResponse(
        meal_name=analysis.meal_name,
        portion_description=analysis.portion_description,
        calories_kcal=analysis.calories_kcal,
        protein_g=analysis.protein_g,
        carbs_g=analysis.carbs_g,
        sugar_g=analysis.sugar_g,
        fat_g=analysis.fat_g,
        saturated_fat_g=analysis.saturated_fat_g,
        fiber_g=analysis.fiber_g,
        confidence_score=analysis.confidence_score,
        identified_items=analysis.identified_items,
        suggested_meal_type=analysis.suggested_meal_type,
        ai_model_version="gpt-4o",
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
        source=meal.source,
        confidence_score=meal.confidence_score,
        image_path=meal.image_path,
        ai_model_version=meal.ai_model_version,
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
        source=meal.source,
        confidence_score=meal.confidence_score,
        image_path=meal.image_path,
        ai_model_version=meal.ai_model_version,
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
        source=updated.source,
        confidence_score=updated.confidence_score,
        image_path=updated.image_path,
        ai_model_version=updated.ai_model_version,
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
