"""
Integration tests for POST /api/v1/onboarding/generate endpoint (ADR-015 Session 3).

Tests cover:
- Happy path: intake → generating → review with generated_setup JSONB
- Wrong status (not intake) → 409
- No active onboarding → 404
- Service timeout → 502, state rolled back to intake
- Validation error → 422, state rolled back to intake
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.onboarding_state import OnboardingState
from app.models.user import User
from app.schemas.onboarding import GeneratedSetup
from app.services.onboarding_generation import (
    SetupGenerationFailed,
    SetupGenerationTimeout,
    SetupValidationError,
)

VALID_SETUP_PAYLOAD = {
    "meal_types": [
        {"name": "Breakfast", "description": "Morning meal", "tags": ["quick"]},
        {"name": "Lunch", "description": "Midday meal", "tags": []},
        {"name": "Dinner", "description": "Evening meal", "tags": ["hearty"]},
    ],
    "day_templates": [
        {
            "name": "Workday",
            "notes": "Standard workday schedule",
            "max_calories_kcal": 2000,
            "max_protein_g": "150.0",
            "slots": [
                {"position": 1, "meal_type_name": "Breakfast"},
                {"position": 2, "meal_type_name": "Lunch"},
                {"position": 3, "meal_type_name": "Dinner"},
            ],
        },
        {
            "name": "Weekend",
            "notes": "Relaxed weekend schedule",
            "slots": [
                {"position": 1, "meal_type_name": "Breakfast"},
                {"position": 2, "meal_type_name": "Lunch"},
                {"position": 3, "meal_type_name": "Dinner"},
            ],
        },
    ],
    "week_plan": {
        "name": "My Week",
        "is_default": True,
        "days": [
            {"weekday": 0, "day_template_name": "Workday"},
            {"weekday": 1, "day_template_name": "Workday"},
            {"weekday": 2, "day_template_name": "Workday"},
            {"weekday": 3, "day_template_name": "Workday"},
            {"weekday": 4, "day_template_name": "Workday"},
            {"weekday": 5, "day_template_name": "Weekend"},
            {"weekday": 6, "day_template_name": "Weekend"},
        ],
    },
}

SAMPLE_INTAKE = {
    "meals_per_day": 3,
    "schedule": "9-5 office job",
}


@pytest_asyncio.fixture
async def client(db: AsyncSession, test_user: User):
    """Create an async HTTP client with database and auth overrides."""

    async def override_get_db():
        yield db

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def intake_onboarding(db: AsyncSession, test_user: User) -> OnboardingState:
    """Create an onboarding in intake status with sample answers."""
    state = OnboardingState(
        user_id=test_user.id,
        status="intake",
        intake_answers=SAMPLE_INTAKE,
    )
    db.add(state)
    await db.flush()
    return state


@pytest_asyncio.fixture
async def review_onboarding(db: AsyncSession, test_user: User) -> OnboardingState:
    """Create an onboarding already in review status."""
    state = OnboardingState(
        user_id=test_user.id,
        status="review",
        intake_answers=SAMPLE_INTAKE,
        generated_setup=VALID_SETUP_PAYLOAD,
    )
    db.add(state)
    await db.flush()
    return state


class TestGenerateEndpoint:
    @pytest.mark.asyncio
    async def test_happy_path_transitions_to_review(
        self, client: AsyncClient, intake_onboarding: OnboardingState, db: AsyncSession
    ):
        setup = GeneratedSetup.model_validate(VALID_SETUP_PAYLOAD)

        with patch(
            "app.api.onboarding.generate_setup",
            new_callable=AsyncMock,
            return_value=setup,
        ):
            resp = await client.post("/api/v1/onboarding/generate")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "review"
        assert data["generated_setup"]["meal_types"][0]["name"] == "Breakfast"
        assert data["generated_setup"]["week_plan"]["name"] == "My Week"
        assert data["error_message"] is None

    @pytest.mark.asyncio
    async def test_wrong_status_returns_409(
        self, client: AsyncClient, review_onboarding: OnboardingState
    ):
        resp = await client.post("/api/v1/onboarding/generate")
        assert resp.status_code == 409
        assert "review" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_no_active_onboarding_returns_404(self, client: AsyncClient):
        resp = await client.post("/api/v1/onboarding/generate")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_timeout_returns_502_and_rolls_back(
        self, client: AsyncClient, intake_onboarding: OnboardingState, db: AsyncSession
    ):
        with patch(
            "app.api.onboarding.generate_setup",
            new_callable=AsyncMock,
            side_effect=SetupGenerationTimeout("timed out"),
        ):
            resp = await client.post("/api/v1/onboarding/generate")

        assert resp.status_code == 502

        # Verify state rolled back to intake with error message
        await db.refresh(intake_onboarding)
        assert intake_onboarding.status == "intake"
        assert intake_onboarding.error_message is not None
        assert "timed out" in intake_onboarding.error_message.lower()

    @pytest.mark.asyncio
    async def test_generation_failed_returns_502_and_rolls_back(
        self, client: AsyncClient, intake_onboarding: OnboardingState, db: AsyncSession
    ):
        with patch(
            "app.api.onboarding.generate_setup",
            new_callable=AsyncMock,
            side_effect=SetupGenerationFailed("API key invalid"),
        ):
            resp = await client.post("/api/v1/onboarding/generate")

        assert resp.status_code == 502

        await db.refresh(intake_onboarding)
        assert intake_onboarding.status == "intake"
        assert intake_onboarding.error_message is not None

    @pytest.mark.asyncio
    async def test_validation_error_returns_422_and_rolls_back(
        self, client: AsyncClient, intake_onboarding: OnboardingState, db: AsyncSession
    ):
        with patch(
            "app.api.onboarding.generate_setup",
            new_callable=AsyncMock,
            side_effect=SetupValidationError(
                "bad data", raw_payload={"broken": True}
            ),
        ):
            resp = await client.post("/api/v1/onboarding/generate")

        assert resp.status_code == 422

        await db.refresh(intake_onboarding)
        assert intake_onboarding.status == "intake"
        assert intake_onboarding.error_message is not None
        assert "invalid" in intake_onboarding.error_message.lower()
