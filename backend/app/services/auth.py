"""Authentication service — register, login, token management, verification, password reset."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.email_token import EmailToken
from app.models.failed_login import FailedLoginAttempt
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.security import (
    create_access_token,
    create_refresh_token,
    create_url_safe_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.services.email import send_password_reset_email, send_verification_email


async def register_user(
    db: AsyncSession, email: str, password: str
) -> User:
    """Create a new user with email/password. Raises 409 if email taken."""
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(password),
        auth_provider="email",
        email_verified=False,
    )
    db.add(user)
    await db.flush()

    # Send verification email
    await _create_and_send_verification_email(db, user)

    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    """Validate credentials and return user. Raises 401/403/423 on failure."""
    # Check account lockout first
    await _check_lockout(db, email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        await _record_failed_login(db, email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.password_hash):
        await _record_failed_login(db, email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox for a verification link.",
        )

    # Successful login — clear failed attempts
    await _clear_failed_logins(db, email)

    return user


async def issue_tokens(
    db: AsyncSession, user: User
) -> tuple[str, str]:
    """Issue an access + refresh token pair. Returns (access_token, raw_refresh_token)."""
    access_token = create_access_token(user.id, user.email)

    raw_refresh = create_refresh_token()
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_record)
    await db.flush()

    return access_token, raw_refresh


async def refresh_tokens(
    db: AsyncSession, raw_refresh_token: str
) -> tuple[str, str, User]:
    """
    Rotate tokens: validate the refresh token, revoke it, issue a new pair.
    Returns (new_access_token, new_raw_refresh_token, user).
    """
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if record.expires_at < datetime.now(timezone.utc):
        record.is_revoked = True
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Revoke old token
    record.is_revoked = True

    # Load user
    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    # Issue new pair
    access_token, raw_refresh = await issue_tokens(db, user)
    return access_token, raw_refresh, user


async def revoke_refresh_token(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke a single refresh token (logout)."""
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record:
        record.is_revoked = True
        await db.flush()


async def revoke_all_user_tokens(db: AsyncSession, user_id: UUID) -> None:
    """Revoke all refresh tokens for a user (logout everywhere)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    for record in result.scalars().all():
        record.is_revoked = True
    await db.flush()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Fetch a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


async def _create_and_send_verification_email(
    db: AsyncSession, user: User
) -> None:
    """Create a verification token and send the verification email."""
    raw_token = create_url_safe_token()
    token_record = EmailToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),  # reuse SHA-256 helper
        token_type="verification",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(token_record)
    await db.flush()
    send_verification_email(user.email, raw_token)


async def resend_verification_email(
    db: AsyncSession, email: str
) -> None:
    """Resend verification email. Silent no-op if email doesn't exist (prevent enumeration)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or user.email_verified:
        return  # Silent — don't reveal whether email exists

    # Invalidate old verification tokens
    old_tokens = await db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == "verification",
            EmailToken.is_used == False,  # noqa: E712
        )
    )
    for t in old_tokens.scalars().all():
        t.is_used = True
    await db.flush()

    await _create_and_send_verification_email(db, user)


async def verify_email(db: AsyncSession, raw_token: str) -> User:
    """Verify email using token. Raises 400 on invalid/expired token."""
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == "verification",
            EmailToken.is_used == False,  # noqa: E712
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used verification token",
        )

    if record.expires_at < datetime.now(timezone.utc):
        record.is_used = True
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one.",
        )

    # Mark token as used
    record.is_used = True

    # Mark user as verified
    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one()
    user.email_verified = True
    await db.flush()

    return user


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Create password reset token and send email. Silent no-op for unknown emails."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return  # Silent — don't reveal whether email exists

    # Invalidate old reset tokens
    old_tokens = await db.execute(
        select(EmailToken).where(
            EmailToken.user_id == user.id,
            EmailToken.token_type == "password_reset",
            EmailToken.is_used == False,  # noqa: E712
        )
    )
    for t in old_tokens.scalars().all():
        t.is_used = True
    await db.flush()

    raw_token = create_url_safe_token()
    token_record = EmailToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_token),
        token_type="password_reset",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(token_record)
    await db.flush()
    send_password_reset_email(user.email, raw_token)


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> User:
    """Reset password using token. Revokes all sessions. Raises 400 on invalid token."""
    token_hash = hash_refresh_token(raw_token)
    result = await db.execute(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.token_type == "password_reset",
            EmailToken.is_used == False,  # noqa: E712
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token",
        )

    if record.expires_at < datetime.now(timezone.utc):
        record.is_used = True
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one.",
        )

    # Mark token as used
    record.is_used = True

    # Update password
    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one()
    user.password_hash = hash_password(new_password)

    # Revoke all refresh tokens (logout everywhere)
    await revoke_all_user_tokens(db, user.id)

    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Account lockout
# ---------------------------------------------------------------------------


async def _check_lockout(db: AsyncSession, email: str) -> None:
    """Check if account is locked due to too many failed login attempts."""
    window_start = datetime.now(timezone.utc) - timedelta(
        minutes=settings.account_lockout_minutes
    )
    result = await db.execute(
        select(func.count())
        .select_from(FailedLoginAttempt)
        .where(
            FailedLoginAttempt.email == email,
            FailedLoginAttempt.attempted_at >= window_start,
        )
    )
    count = result.scalar()
    if count >= settings.account_lockout_attempts:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to too many failed login attempts. Try again later.",
        )


async def _record_failed_login(db: AsyncSession, email: str) -> None:
    """Record a failed login attempt."""
    db.add(FailedLoginAttempt(email=email))
    await db.flush()


async def _clear_failed_logins(db: AsyncSession, email: str) -> None:
    """Clear failed login attempts after successful login."""
    await db.execute(
        delete(FailedLoginAttempt).where(FailedLoginAttempt.email == email)
    )
    await db.flush()
