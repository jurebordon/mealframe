"""Pydantic schemas for authentication endpoints."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .base import BaseSchema


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    email: EmailStr
    password: str


class TokenResponse(BaseSchema):
    """Response for login and refresh — contains access token."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseSchema):
    """Public user profile returned by GET /auth/me."""

    id: UUID
    email: str
    email_verified: bool
    auth_provider: str
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    """Request body for POST /auth/forgot-password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request body for POST /auth/reset-password."""

    token: str
    password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    """Request body for POST /auth/verify-email."""

    token: str


class MessageResponse(BaseSchema):
    """Generic message response."""

    message: str
