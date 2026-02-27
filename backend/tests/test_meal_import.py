"""
Integration tests for the CSV meal import endpoint.

Tests cover:
- POST /api/v1/meals/import - CSV file upload and meal creation

These tests verify:
- Valid CSV with all columns creates meals correctly
- Missing optional fields result in null values
- Missing required fields skip the row and report errors
- Unknown meal types are auto-created and assigned (info message logged)
- Empty file / malformed CSV returns appropriate errors
- Meal type associations are created correctly
- Duplicate meal names are allowed
- Trailing blank rows are ignored
"""
import io
from uuid import uuid4


def _uid() -> str:
    """Short unique suffix for test isolation."""
    return uuid4().hex[:8]

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Meal, MealType, User
from app.models.meal_to_meal_type import meal_to_meal_type
from app.database import get_db


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Create an async HTTP client with database override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def meal_types(db: AsyncSession, test_user: User) -> dict[str, MealType]:
    """Create meal types that match the frozen spec defaults."""
    suffix = uuid4().hex[:8]
    names = ["Breakfast", "Lunch", "Dinner", "Weekend Breakfast", "Hiking Fuel"]
    types = {}
    for name in names:
        mt = MealType(
            id=uuid4(),
            user_id=test_user.id,
            name=f"{name} {suffix}",
            description=f"Test {name}",
        )
        db.add(mt)
        types[name] = mt
    await db.flush()
    return types


def _make_csv(header: str, *rows: str) -> bytes:
    """Helper to build CSV bytes from header + row strings."""
    lines = [header] + list(rows)
    return "\n".join(lines).encode("utf-8")


# --- Happy Path Tests ---


@pytest.mark.asyncio
async def test_import_valid_csv_all_columns(
    client: AsyncClient, db: AsyncSession, meal_types: dict[str, MealType],
):
    """Full CSV with all columns creates meals with associations and macros."""
    breakfast_name = meal_types["Breakfast"].name
    lunch_name = meal_types["Lunch"].name
    uid = _uid()

    csv_data = _make_csv(
        "name,portion_description,calories_kcal,protein_g,carbs_g,fat_g,meal_types,notes",
        f'"Scrambled Eggs {uid}","2 eggs + 1 slice toast",320,18,15,22,"{breakfast_name}","Use whole wheat"',
        f'"Chicken Bowl {uid}","150g chicken + rice",520,42,50,12,"{lunch_name}","Meal prep friendly"',
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["total_rows"] == 2
    assert data["summary"]["created"] == 2
    assert data["summary"]["skipped"] == 0
    assert data["summary"]["warnings"] == 0
    assert data["warnings"] == []
    assert data["errors"] == []

    # Verify meals exist in database
    result = await db.execute(select(Meal).where(Meal.name == f"Scrambled Eggs {uid}"))
    meal = result.scalars().first()
    assert meal is not None
    assert meal.portion_description == "2 eggs + 1 slice toast"
    assert meal.calories_kcal == 320
    assert meal.notes == "Use whole wheat"

    # Verify meal type association
    assoc_result = await db.execute(
        select(meal_to_meal_type).where(meal_to_meal_type.c.meal_id == meal.id)
    )
    assocs = assoc_result.all()
    assert len(assocs) == 1
    assert assocs[0].meal_type_id == meal_types["Breakfast"].id


@pytest.mark.asyncio
async def test_import_required_fields_only(client: AsyncClient, db: AsyncSession):
    """CSV with only required columns (name, portion_description) works."""
    csv_data = _make_csv(
        "name,portion_description",
        "Simple Meal,1 bowl of rice",
        "Another Meal,2 eggs scrambled",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["created"] == 2

    # Verify null optional fields
    result = await db.execute(select(Meal).where(Meal.name == "Simple Meal"))
    meal = result.scalars().first()
    assert meal is not None
    assert meal.calories_kcal is None
    assert meal.protein_g is None
    assert meal.notes is None


@pytest.mark.asyncio
async def test_import_multiple_meal_types(
    client: AsyncClient, db: AsyncSession, meal_types: dict[str, MealType],
):
    """A meal assigned to multiple meal types gets all associations."""
    breakfast_name = meal_types["Breakfast"].name
    weekend_name = meal_types["Weekend Breakfast"].name
    uid = _uid()
    meal_name = f"Full Breakfast {uid}"

    csv_data = _make_csv(
        "name,portion_description,meal_types",
        f'"{meal_name}","Eggs + bacon + toast","{breakfast_name},{weekend_name}"',
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["created"] == 1
    assert data["summary"]["warnings"] == 0

    # Verify both associations
    result = await db.execute(select(Meal).where(Meal.name == meal_name))
    meal = result.scalars().first()
    assert meal is not None
    assoc_result = await db.execute(
        select(meal_to_meal_type).where(meal_to_meal_type.c.meal_id == meal.id)
    )
    assocs = assoc_result.all()
    assert len(assocs) == 2


@pytest.mark.asyncio
async def test_import_duplicate_names_allowed(client: AsyncClient, db: AsyncSession):
    """Duplicate meal names create separate meals (per MEAL_IMPORT_GUIDE.md)."""
    csv_data = _make_csv(
        "name,portion_description",
        "Oatmeal,60g oats + milk",
        "Oatmeal,80g oats + protein powder",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["created"] == 2

    result = await db.execute(
        select(func.count()).select_from(Meal).where(Meal.name == "Oatmeal")
    )
    count = result.scalar()
    assert count == 2


# --- Warning Tests ---


@pytest.mark.asyncio
async def test_import_unknown_meal_type_warns(client: AsyncClient, db: AsyncSession):
    """Unknown meal type is auto-created and info message logged."""
    csv_data = _make_csv(
        "name,portion_description,meal_types",
        '"Snack","A handful of nuts","Nonexistent Type"',
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["created"] == 1
    assert data["summary"]["warnings"] == 1
    assert len(data["warnings"]) == 1
    assert data["warnings"][0]["row"] == 1
    assert "Nonexistent Type" in data["warnings"][0]["message"]
    assert "Created new meal type" in data["warnings"][0]["message"]

    # Meal type was created
    assert data["summary"]["created_meal_types"] == ["Nonexistent Type"]

    # Meal was created with meal type association
    result = await db.execute(select(Meal).where(Meal.name == "Snack"))
    meal = result.scalars().first()
    assert meal is not None

    # Verify meal type was created
    mt_result = await db.execute(select(MealType).where(MealType.name == "Nonexistent Type"))
    meal_type = mt_result.scalars().first()
    assert meal_type is not None

    # Verify association
    assoc_result = await db.execute(
        select(meal_to_meal_type).where(meal_to_meal_type.c.meal_id == meal.id)
    )
    assocs = assoc_result.all()
    assert len(assocs) == 1
    assert assocs[0].meal_type_id == meal_type.id


@pytest.mark.asyncio
async def test_import_invalid_numeric_warns(client: AsyncClient, db: AsyncSession):
    """Invalid numeric values create warnings and import with null."""
    csv_data = _make_csv(
        "name,portion_description,calories_kcal,protein_g",
        '"Meal","Some portion",not_a_number,abc',
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["created"] == 1
    assert data["summary"]["warnings"] == 2
    assert len(data["warnings"]) == 2

    result = await db.execute(select(Meal).where(Meal.name == "Meal"))
    meal = result.scalars().first()
    assert meal.calories_kcal is None
    assert meal.protein_g is None


# --- Error Tests ---


@pytest.mark.asyncio
async def test_import_missing_name_skips_row(client: AsyncClient, db: AsyncSession):
    """Missing name field skips the row with an error."""
    csv_data = _make_csv(
        "name,portion_description",
        ",Some portion",  # Empty name
        "Valid Meal,Good portion",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["created"] == 1
    assert data["summary"]["skipped"] == 1
    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 1
    assert "name" in data["errors"][0]["message"]


@pytest.mark.asyncio
async def test_import_missing_portion_skips_row(client: AsyncClient, db: AsyncSession):
    """Missing portion_description field skips the row with an error."""
    csv_data = _make_csv(
        "name,portion_description",
        "No Portion,",  # Empty portion
        "Good Meal,With portion",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["created"] == 1
    assert data["summary"]["skipped"] == 1
    assert len(data["errors"]) == 1
    assert "portion_description" in data["errors"][0]["message"]


@pytest.mark.asyncio
async def test_import_missing_required_column(client: AsyncClient):
    """CSV missing a required column header fails immediately."""
    csv_data = _make_csv(
        "name,calories_kcal",  # Missing portion_description column
        "Eggs,320",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["summary"]["created"] == 0
    assert len(data["errors"]) == 1
    assert "portion_description" in data["errors"][0]["message"]


@pytest.mark.asyncio
async def test_import_empty_file(client: AsyncClient):
    """Empty CSV file returns 400 error."""
    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(b""), "text/csv")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_import_header_only(client: AsyncClient):
    """CSV with only header row creates no meals."""
    csv_data = _make_csv(
        "name,portion_description,calories_kcal",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["total_rows"] == 0
    assert data["summary"]["created"] == 0


@pytest.mark.asyncio
async def test_import_trailing_blank_rows_ignored(client: AsyncClient, db: AsyncSession):
    """Trailing blank rows in CSV are ignored."""
    csv_data = _make_csv(
        "name,portion_description",
        "Valid Meal,Good portion",
        "",
        "  ",
        "",
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["created"] == 1
    assert data["summary"]["total_rows"] == 1


# --- Mixed Success/Error Tests ---


@pytest.mark.asyncio
async def test_import_mixed_valid_and_invalid_rows(
    client: AsyncClient, db: AsyncSession, meal_types: dict[str, MealType],
):
    """Mix of valid and invalid rows: valid rows imported, invalid rows skipped with errors."""
    breakfast_name = meal_types["Breakfast"].name

    csv_data = _make_csv(
        "name,portion_description,calories_kcal,meal_types",
        f'"Eggs","2 eggs scrambled",320,"{breakfast_name}"',  # Valid
        ',"Missing name portion",200,""',  # Missing name → error
        f'"No Portion","",0,"{breakfast_name}"',  # Empty portion → error
        '"Snack","Handful of nuts",150,"Unknown Type"',  # Unknown type → warning, still created
    )

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_data), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["total_rows"] == 4
    assert data["summary"]["created"] == 2  # Eggs + Snack
    assert data["summary"]["skipped"] == 2  # Row 2 (no name) + Row 3 (no portion)
    assert data["summary"]["warnings"] == 1  # Unknown Type
    assert len(data["errors"]) == 2
    assert len(data["warnings"]) == 1


# --- BOM Handling Test ---


@pytest.mark.asyncio
async def test_import_utf8_bom(client: AsyncClient, db: AsyncSession):
    """CSV saved from Excel with UTF-8 BOM is handled correctly."""
    uid = _uid()
    # Excel saves UTF-8 CSV with BOM: encode plain text with utf-8-sig to add BOM bytes
    csv_content = f'name,portion_description\nBOM Meal {uid},1 portion'
    csv_bytes = csv_content.encode("utf-8-sig")  # Adds BOM prefix bytes

    response = await client.post(
        "/api/v1/meals/import",
        files={"file": ("meals.csv", io.BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["created"] == 1

    result = await db.execute(select(Meal).where(Meal.name == f"BOM Meal {uid}"))
    assert result.scalars().first() is not None
