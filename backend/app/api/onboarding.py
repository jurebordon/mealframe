"""API routes for onboarding state management (ADR-015)."""
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
