"""Service layer for onboarding state management (ADR-015)."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.onboarding_state import OnboardingState
from ..schemas.onboarding import OnboardingStateUpdate

# Terminal statuses that allow a new onboarding to be created
_TERMINAL_STATUSES = ("completed", "abandoned")

# Valid state transitions: current_status -> set of allowed next statuses
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "intake": {"generating", "abandoned"},
    "generating": {"review", "intake", "abandoned"},
    "review": {"meal_import", "intake", "abandoned"},
    "meal_import": {"applying", "abandoned"},
    "applying": {"completed", "meal_import", "abandoned"},
}


async def get_active_onboarding(
    db: AsyncSession, user_id: UUID
) -> OnboardingState | None:
    """Get the user's active (non-terminal) onboarding state, if any."""
    result = await db.execute(
        select(OnboardingState).where(
            OnboardingState.user_id == user_id,
            OnboardingState.status.notin_(_TERMINAL_STATUSES),
        )
    )
    return result.scalar_one_or_none()


async def create_onboarding(
    db: AsyncSession, user_id: UUID
) -> OnboardingState:
    """Start a new onboarding. Raises ValueError if one is already active."""
    existing = await get_active_onboarding(db, user_id)
    if existing:
        raise ValueError("An active onboarding already exists")

    state = OnboardingState(user_id=user_id)
    db.add(state)
    await db.flush()
    return state


async def update_onboarding(
    db: AsyncSession, user_id: UUID, data: OnboardingStateUpdate
) -> OnboardingState | None:
    """Update the active onboarding state. Returns None if no active onboarding."""
    state = await get_active_onboarding(db, user_id)
    if not state:
        return None

    # Validate status transition if status is being changed
    if data.status is not None and data.status != state.status:
        allowed = _VALID_TRANSITIONS.get(state.status, set())
        if data.status not in allowed:
            raise ValueError(
                f"Invalid status transition from '{state.status}' to '{data.status}'"
            )
        state.status = data.status

    if data.intake_substep is not None:
        state.intake_substep = data.intake_substep
    if data.intake_answers is not None:
        state.intake_answers = data.intake_answers
    if data.generated_setup is not None:
        state.generated_setup = data.generated_setup
    if data.chat_messages is not None:
        state.chat_messages = data.chat_messages
    if data.imported_meals is not None:
        state.imported_meals = data.imported_meals
    if data.error_message is not None:
        state.error_message = data.error_message

    db.add(state)
    await db.flush()
    return state


async def abandon_onboarding(
    db: AsyncSession, user_id: UUID
) -> bool:
    """Abandon the active onboarding. Returns False if none found."""
    state = await get_active_onboarding(db, user_id)
    if not state:
        return False

    state.status = "abandoned"
    db.add(state)
    await db.flush()
    return True


async def get_onboarding_status(
    db: AsyncSession, user_id: UUID
) -> tuple[bool, bool]:
    """Check onboarding status. Returns (has_completed, has_active)."""
    result = await db.execute(
        select(OnboardingState.status).where(OnboardingState.user_id == user_id)
    )
    statuses = [row[0] for row in result.all()]

    has_completed = "completed" in statuses
    has_active = any(s not in _TERMINAL_STATUSES for s in statuses)
    return has_completed, has_active
