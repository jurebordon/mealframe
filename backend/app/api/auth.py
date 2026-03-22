"""Authentication API endpoints (ADR-014)."""
import logging

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    GoogleOAuthEnabledResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth import (
    authenticate_user,
    issue_tokens,
    refresh_tokens,
    register_user,
    request_password_reset,
    resend_verification_email,
    reset_password,
    revoke_refresh_token,
    verify_email,
)
from app.services.oauth import (
    build_authorization_url,
    exchange_code_for_user_info,
    get_or_create_google_user,
    google_oauth_enabled,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)

# Cookie settings for refresh token
_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days in seconds


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    """Set the refresh token as an HTTP-only secure cookie."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=raw_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/api/v1/auth",  # Only sent to auth endpoints
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=_REFRESH_COOKIE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit(settings.register_rate_limit)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new account. A verification email is sent automatically.
    User must verify their email before they can log in.
    """
    await register_user(db, body.email, body.password)
    return MessageResponse(
        message="Account created. Please check your email to verify your account."
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.login_rate_limit)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email/password and return tokens."""
    user = await authenticate_user(db, body.email, body.password)
    access_token, raw_refresh = await issue_tokens(db, user)
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue a new access token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    access_token, raw_refresh, _user = await refresh_tokens(db, refresh_token)
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=_REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    """Revoke the current refresh token and clear the cookie."""
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_endpoint(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify email address using the token from the verification email."""
    await verify_email(db, body.token)
    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit(settings.password_reset_rate_limit)
async def resend_verification(
    request: Request,
    body: ForgotPasswordRequest,  # reuse — it's just an email field
    db: AsyncSession = Depends(get_db),
):
    """Resend verification email. Always returns success to prevent email enumeration."""
    await resend_verification_email(db, body.email)
    return MessageResponse(
        message="If an unverified account exists with that email, a verification link has been sent."
    )


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(settings.password_reset_rate_limit)
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset email. Always returns success to prevent email enumeration."""
    await request_password_reset(db, body.email)
    return MessageResponse(
        message="If an account exists with that email, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_endpoint(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using the token from the reset email. Invalidates all sessions."""
    await reset_password(db, body.token, body.password)
    return MessageResponse(
        message="Password reset successfully. Please log in with your new password."
    )


# ---------------------------------------------------------------------------
# Google OAuth (ADR-014 Session 6)
# ---------------------------------------------------------------------------

# State tokens stored in-memory (short-lived, cleared on use).
# For a single-server deployment this is sufficient.
_oauth_states: dict[str, bool] = {}


@router.get("/google/enabled", response_model=GoogleOAuthEnabledResponse)
async def google_enabled():
    """Check if Google OAuth is configured. Frontend uses this to show/hide button."""
    return GoogleOAuthEnabledResponse(enabled=google_oauth_enabled())


@router.get("/google/authorize")
async def google_authorize(request: Request):
    """Redirect user to Google consent screen."""
    if not google_oauth_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google OAuth is not configured",
        )

    # Build callback URL from the current request
    redirect_uri = str(request.url_for("google_callback"))
    authorization_url, state = await build_authorization_url(redirect_uri)

    # Store state for CSRF validation
    _oauth_states[state] = True

    return RedirectResponse(url=authorization_url, status_code=302)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback. Exchanges code, creates/links user, redirects to frontend."""
    # Validate CSRF state
    if not _oauth_states.pop(state, False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state parameter",
        )

    redirect_uri = str(request.url_for("google_callback"))

    try:
        google_info = await exchange_code_for_user_info(code, redirect_uri)
    except Exception:
        logger.exception("Google OAuth code exchange failed")
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{settings.frontend_url}/oauth/callback?error=exchange_failed",
            status_code=302,
        )

    user = await get_or_create_google_user(db, google_info)

    if not user.is_active:
        return RedirectResponse(
            url=f"{settings.frontend_url}/oauth/callback?error=account_disabled",
            status_code=302,
        )

    # Issue tokens
    access_token, raw_refresh = await issue_tokens(db, user)

    # Redirect to frontend callback page with access token
    response = RedirectResponse(
        url=f"{settings.frontend_url}/oauth/callback?token={access_token}",
        status_code=302,
    )
    _set_refresh_cookie(response, raw_refresh)
    return response
