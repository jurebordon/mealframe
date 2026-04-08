"""
Integration tests for the Onboarding State CRUD API endpoints.

Tests cover:
- GET /api/v1/onboarding/state - Get active onboarding
- POST /api/v1/onboarding/state - Start new onboarding
- PATCH /api/v1/onboarding/state - Update onboarding state
- DELETE /api/v1/onboarding/state - Abandon onboarding
- GET /api/v1/onboarding/status - Check onboarding completion/active status
"""
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.main import app
from app.models.onboarding_state import OnboardingState
from app.models.user import User


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
async def active_onboarding(db: AsyncSession, test_user: User) -> OnboardingState:
    """Create an active onboarding state for testing."""
    state = OnboardingState(user_id=test_user.id)
    db.add(state)
    await db.flush()
    return state


@pytest_asyncio.fixture
async def completed_onboarding(db: AsyncSession, test_user: User) -> OnboardingState:
    """Create a completed onboarding state for testing."""
    state = OnboardingState(user_id=test_user.id, status="completed")
    db.add(state)
    await db.flush()
    return state


# --- GET /api/v1/onboarding/state ---


class TestGetState:
    async def test_returns_active_onboarding(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.get("/api/v1/onboarding/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(active_onboarding.id)
        assert data["status"] == "intake"
        assert data["intake_substep"] == 1
        assert data["intake_answers"] == {}
        assert data["generated_setup"] == {}
        assert data["chat_messages"] == []
        assert data["imported_meals"] == []

    async def test_no_active_returns_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/onboarding/state")
        assert resp.status_code == 404

    async def test_ignores_completed(self, client: AsyncClient, completed_onboarding: OnboardingState):
        resp = await client.get("/api/v1/onboarding/state")
        assert resp.status_code == 404


# --- POST /api/v1/onboarding/state ---


class TestCreateState:
    async def test_creates_with_defaults(self, client: AsyncClient):
        resp = await client.post("/api/v1/onboarding/state")
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "intake"
        assert data["intake_substep"] == 1
        assert data["intake_answers"] == {}
        assert data["generated_setup"] == {}
        assert data["chat_messages"] == []
        assert data["imported_meals"] == []
        assert data["error_message"] is None

    async def test_conflict_when_active_exists(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.post("/api/v1/onboarding/state")
        assert resp.status_code == 409

    async def test_succeeds_after_completed(self, client: AsyncClient, completed_onboarding: OnboardingState):
        resp = await client.post("/api/v1/onboarding/state")
        assert resp.status_code == 201
        assert resp.json()["status"] == "intake"


# --- PATCH /api/v1/onboarding/state ---


class TestUpdateState:
    async def test_update_intake_answers(self, client: AsyncClient, active_onboarding: OnboardingState):
        answers = {"meal_count": 3, "schedule": "standard"}
        resp = await client.patch("/api/v1/onboarding/state", json={"intake_answers": answers})
        assert resp.status_code == 200
        assert resp.json()["intake_answers"] == answers

    async def test_update_substep(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.patch("/api/v1/onboarding/state", json={"intake_substep": 3})
        assert resp.status_code == 200
        assert resp.json()["intake_substep"] == 3

    async def test_valid_status_transition(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.patch("/api/v1/onboarding/state", json={"status": "generating"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "generating"

    async def test_invalid_status_transition_returns_422(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.patch("/api/v1/onboarding/state", json={"status": "completed"})
        assert resp.status_code == 422
        assert "Invalid status transition" in resp.json()["detail"]

    async def test_no_active_returns_404(self, client: AsyncClient):
        resp = await client.patch("/api/v1/onboarding/state", json={"intake_substep": 2})
        assert resp.status_code == 404


# --- DELETE /api/v1/onboarding/state ---


class TestDeleteState:
    async def test_abandons_onboarding(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.delete("/api/v1/onboarding/state")
        assert resp.status_code == 204

        # Verify it's gone
        resp = await client.get("/api/v1/onboarding/state")
        assert resp.status_code == 404

    async def test_no_active_returns_404(self, client: AsyncClient):
        resp = await client.delete("/api/v1/onboarding/state")
        assert resp.status_code == 404

    async def test_can_create_after_abandon(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.delete("/api/v1/onboarding/state")
        assert resp.status_code == 204

        resp = await client.post("/api/v1/onboarding/state")
        assert resp.status_code == 201


# --- GET /api/v1/onboarding/status ---


class TestGetStatus:
    async def test_no_onboarding(self, client: AsyncClient):
        resp = await client.get("/api/v1/onboarding/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_completed"] is False
        assert data["has_active"] is False

    async def test_active_onboarding(self, client: AsyncClient, active_onboarding: OnboardingState):
        resp = await client.get("/api/v1/onboarding/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_completed"] is False
        assert data["has_active"] is True

    async def test_completed_onboarding(self, client: AsyncClient, completed_onboarding: OnboardingState):
        resp = await client.get("/api/v1/onboarding/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_completed"] is True
        assert data["has_active"] is False
