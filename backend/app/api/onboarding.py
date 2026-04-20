"""API routes for onboarding state management (ADR-015)."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.onboarding import (
    OnboardingStateResponse,
    OnboardingStateUpdate,
    OnboardingStatusResponse,
)
from ..services.onboarding import (
    abandon_onboarding,
    create_onboarding,
    get_active_onboarding,
    get_onboarding_status,
    update_onboarding,
)
from ..services.onboarding_generation import (
    SetupGenerationFailed,
    SetupGenerationTimeout,
    SetupValidationError,
    generate_setup,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["Onboarding"])


@router.get("/state", response_model=OnboardingStateResponse)
async def get_state(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OnboardingStateResponse:
    """Get the user's active onboarding state."""
    state = await get_active_onboarding(db, user.id)
    if not state:
        raise HTTPException(status_code=404, detail="No active onboarding")
    return OnboardingStateResponse.model_validate(state)


@router.post("/state", response_model=OnboardingStateResponse, status_code=201)
async def create_state(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OnboardingStateResponse:
    """Start a new onboarding. Returns 409 if one is already active."""
    try:
        state = await create_onboarding(db, user.id)
    except ValueError:
        raise HTTPException(status_code=409, detail="An active onboarding already exists")
    return OnboardingStateResponse.model_validate(state)


@router.patch("/state", response_model=OnboardingStateResponse)
async def update_state(
    data: OnboardingStateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OnboardingStateResponse:
    """Update the active onboarding state."""
    try:
        state = await update_onboarding(db, user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not state:
        raise HTTPException(status_code=404, detail="No active onboarding")
    return OnboardingStateResponse.model_validate(state)


@router.delete("/state", status_code=204)
async def delete_state(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Abandon the active onboarding."""
    abandoned = await abandon_onboarding(db, user.id)
    if not abandoned:
        raise HTTPException(status_code=404, detail="No active onboarding")


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OnboardingStatusResponse:
    """Check whether the user has completed onboarding or has one in progress."""
    has_completed, has_active = await get_onboarding_status(db, user.id)
    return OnboardingStatusResponse(has_completed=has_completed, has_active=has_active)


@router.post("/generate", response_model=OnboardingStateResponse)
async def generate_onboarding_setup(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OnboardingStateResponse:
    """Generate AI meal planning setup from intake answers.

    Transitions intake → generating → review on success.
    Rolls back to intake on failure.
    """
    state = await get_active_onboarding(db, user.id)
    if not state:
        raise HTTPException(status_code=404, detail="No active onboarding")
    if state.status != "intake":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot generate from status '{state.status}', expected 'intake'",
        )

    # Transition to generating
    state.status = "generating"
    state.error_message = None
    db.add(state)
    await db.flush()

    try:
        result = await generate_setup(state.intake_answers)
    except SetupGenerationTimeout as e:
        logger.warning("Setup generation timed out for user %s: %s", user.id, e)
        state.status = "intake"
        state.error_message = "AI generation timed out. Please try again."
        db.add(state)
        await db.flush()
        raise HTTPException(status_code=502, detail=str(e))
    except SetupGenerationFailed as e:
        logger.error("Setup generation failed for user %s: %s", user.id, e)
        state.status = "intake"
        state.error_message = "AI generation failed. Please try again."
        db.add(state)
        await db.flush()
        raise HTTPException(status_code=502, detail=str(e))
    except SetupValidationError as e:
        logger.error(
            "Setup validation failed for user %s: %s | raw: %s",
            user.id, e, e.raw_payload,
        )
        state.status = "intake"
        state.error_message = "AI generated an invalid setup. Please try again."
        db.add(state)
        await db.flush()
        raise HTTPException(status_code=422, detail=str(e))

    # Success — persist and transition to review
    state.generated_setup = result.model_dump(mode="json")
    state.status = "review"
    state.error_message = None
    db.add(state)
    await db.flush()

    return OnboardingStateResponse.model_validate(state)
