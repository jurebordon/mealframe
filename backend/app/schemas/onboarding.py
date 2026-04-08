"""Pydantic schemas for onboarding state API."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from .base import BaseSchema


class OnboardingStateResponse(BaseSchema):
    """Full onboarding state returned by GET/POST/PATCH endpoints."""

    id: UUID
    status: str
    intake_substep: int | None = None
    intake_answers: dict[str, Any] = Field(default_factory=dict)
    generated_setup: dict[str, Any] = Field(default_factory=dict)
    chat_messages: list[dict[str, Any]] = Field(default_factory=list)
    imported_meals: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class OnboardingStateUpdate(BaseSchema):
    """Partial update for PATCH endpoint. All fields optional."""

    status: str | None = None
    intake_substep: int | None = Field(default=None, ge=1, le=6)
    intake_answers: dict[str, Any] | None = None
    generated_setup: dict[str, Any] | None = None
    chat_messages: list[dict[str, Any]] | None = None
    imported_meals: list[dict[str, Any]] | None = None
    error_message: str | None = None


class OnboardingStatusResponse(BaseSchema):
    """Lightweight check for frontend routing."""

    has_completed: bool
    has_active: bool
