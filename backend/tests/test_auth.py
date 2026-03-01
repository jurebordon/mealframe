"""
Integration tests for authentication endpoints (ADR-014).

Tests cover:
- POST /api/v1/auth/register — create account, send verification email
- POST /api/v1/auth/verify-email — verify email with token
- POST /api/v1/auth/resend-verification — resend verification email
- POST /api/v1/auth/login — authenticate, get tokens
- POST /api/v1/auth/refresh — rotate refresh token
- POST /api/v1/auth/logout — revoke refresh token
- GET /api/v1/auth/me — get current user profile
- POST /api/v1/auth/forgot-password — request password reset
- POST /api/v1/auth/reset-password — reset password with token
- Account lockout after failed login attempts
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app
from app.models.email_token import EmailToken
from app.models.user import User
from app.security import hash_password


AUTH_PREFIX = "/api/v1/auth"


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Create an async HTTP client with database override and no rate limits."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Disable rate limiting for tests
    from app.api.auth import limiter
    limiter.enabled = False

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    limiter.enabled = True
    app.dependency_overrides.clear()


async def _register_and_verify(
    client: AsyncClient, db: AsyncSession, email: str, password: str = "securepass123"
) -> dict:
    """Helper: register a user, auto-verify, and login. Returns login response JSON."""
    # Register
    resp = await client.post(
        f"{AUTH_PREFIX}/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201

    # Auto-verify the user directly in DB
    await db.execute(
        update(User).where(User.email == email).values(email_verified=True)
    )
    await db.flush()

    # Login
    login_resp = await client.post(
        f"{AUTH_PREFIX}/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    return login_resp


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "new@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "message" in body
        assert "verify" in body["message"].lower()
        # No tokens — user must verify first
        assert "access_token" not in body

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "dup@example.com", "password": "securepass123"}
        resp1 = await client.post(f"{AUTH_PREFIX}/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post(f"{AUTH_PREFIX}/register", json=payload)
        assert resp2.status_code == 409
        assert "already registered" in resp2.json()["detail"]

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "short@example.com", "password": "abc"},
        )
        assert resp.status_code == 422  # Pydantic validation

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "not-an-email", "password": "securepass123"},
        )
        assert resp.status_code == 422

    async def test_register_creates_verification_token(
        self, client: AsyncClient, db: AsyncSession
    ):
        resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "verify-check@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 201

        # Verify a token was created for this user
        user_result = await db.execute(
            select(User).where(User.email == "verify-check@example.com")
        )
        user = user_result.scalar_one()
        token_result = await db.execute(
            select(EmailToken).where(
                EmailToken.user_id == user.id,
                EmailToken.token_type == "verification",
            )
        )
        token = token_result.scalar_one()
        assert not token.is_used


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------


class TestEmailVerification:
    async def test_verify_email_success(self, client: AsyncClient, db: AsyncSession):
        # Register
        await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "toverify@example.com", "password": "securepass123"},
        )

        # Get the raw token from the email_token table (in real life, from email)
        user_result = await db.execute(
            select(User).where(User.email == "toverify@example.com")
        )
        user = user_result.scalar_one()
        assert not user.email_verified

        token_result = await db.execute(
            select(EmailToken).where(
                EmailToken.user_id == user.id,
                EmailToken.token_type == "verification",
            )
        )
        token_record = token_result.scalar_one()

        # We need the raw token, not the hash. Since we can't get it from the hash,
        # create a known token for testing.
        from app.security import create_url_safe_token, hash_refresh_token
        from datetime import datetime, timedelta, timezone

        raw_token = create_url_safe_token()
        # Mark old token as used and create a new one we control
        token_record.is_used = True
        new_token = EmailToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            token_type="verification",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(new_token)
        await db.flush()

        # Verify
        resp = await client.post(
            f"{AUTH_PREFIX}/verify-email",
            json={"token": raw_token},
        )
        assert resp.status_code == 200
        assert "verified" in resp.json()["message"].lower()

        # User should now be verified
        await db.refresh(user)
        assert user.email_verified

    async def test_verify_email_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            f"{AUTH_PREFIX}/verify-email",
            json={"token": "invalid-token"},
        )
        assert resp.status_code == 400

    async def test_verify_email_expired_token(
        self, client: AsyncClient, db: AsyncSession
    ):
        from app.security import create_url_safe_token, hash_refresh_token
        from datetime import datetime, timedelta, timezone

        # Create a user
        await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "expired-verify@example.com", "password": "securepass123"},
        )
        user_result = await db.execute(
            select(User).where(User.email == "expired-verify@example.com")
        )
        user = user_result.scalar_one()

        # Create an expired token
        raw_token = create_url_safe_token()
        expired_token = EmailToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            token_type="verification",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(expired_token)
        await db.flush()

        resp = await client.post(
            f"{AUTH_PREFIX}/verify-email",
            json={"token": raw_token},
        )
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    async def test_resend_verification(self, client: AsyncClient, db: AsyncSession):
        await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "resend@example.com", "password": "securepass123"},
        )

        resp = await client.post(
            f"{AUTH_PREFIX}/resend-verification",
            json={"email": "resend@example.com"},
        )
        assert resp.status_code == 200

        # Should have 2 tokens: original (marked used) + new one
        user_result = await db.execute(
            select(User).where(User.email == "resend@example.com")
        )
        user = user_result.scalar_one()
        tokens = await db.execute(
            select(EmailToken).where(
                EmailToken.user_id == user.id,
                EmailToken.token_type == "verification",
            )
        )
        all_tokens = tokens.scalars().all()
        assert len(all_tokens) == 2
        # One should be used (old), one should be fresh
        used = [t for t in all_tokens if t.is_used]
        fresh = [t for t in all_tokens if not t.is_used]
        assert len(used) == 1
        assert len(fresh) == 1

    async def test_resend_verification_nonexistent_email(self, client: AsyncClient):
        """Should return success even for nonexistent emails (prevent enumeration)."""
        resp = await client.post(
            f"{AUTH_PREFIX}/resend-verification",
            json={"email": "nobody@example.com"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    async def test_login_success(self, client: AsyncClient, db: AsyncSession):
        login_resp = await _register_and_verify(client, db, "login@example.com")
        body = login_resp.json()
        assert "access_token" in body
        assert "refresh_token" in login_resp.cookies

    async def test_login_unverified_email(self, client: AsyncClient):
        # Register but don't verify
        await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "unverified@example.com", "password": "securepass123"},
        )

        resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "unverified@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 403
        assert "not verified" in resp.json()["detail"].lower()

    async def test_login_wrong_password(self, client: AsyncClient, db: AsyncSession):
        await _register_and_verify(client, db, "wrong@example.com")

        resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "wrong@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------


class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient, db: AsyncSession):
        login_resp = await _register_and_verify(client, db, "refresh@example.com")
        refresh_cookie = login_resp.cookies.get("refresh_token")
        assert refresh_cookie is not None

        resp = await client.post(
            f"{AUTH_PREFIX}/refresh",
            cookies={"refresh_token": refresh_cookie},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.cookies

    async def test_refresh_reuse_revoked_token(
        self, client: AsyncClient, db: AsyncSession
    ):
        """After refresh, the old refresh token should be revoked."""
        login_resp = await _register_and_verify(client, db, "reuse@example.com")
        old_refresh = login_resp.cookies.get("refresh_token")

        # Use it once — should work
        resp1 = await client.post(
            f"{AUTH_PREFIX}/refresh",
            cookies={"refresh_token": old_refresh},
        )
        assert resp1.status_code == 200

        # Use old token again — should fail (revoked)
        resp2 = await client.post(
            f"{AUTH_PREFIX}/refresh",
            cookies={"refresh_token": old_refresh},
        )
        assert resp2.status_code == 401

    async def test_refresh_no_cookie(self, client: AsyncClient):
        resp = await client.post(f"{AUTH_PREFIX}/refresh")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class TestLogout:
    async def test_logout_clears_cookie(
        self, client: AsyncClient, db: AsyncSession
    ):
        login_resp = await _register_and_verify(client, db, "logout@example.com")
        refresh_cookie = login_resp.cookies.get("refresh_token")

        resp = await client.post(
            f"{AUTH_PREFIX}/logout",
            cookies={"refresh_token": refresh_cookie},
        )
        assert resp.status_code == 204

        # Refresh token should be revoked now
        resp2 = await client.post(
            f"{AUTH_PREFIX}/refresh",
            cookies={"refresh_token": refresh_cookie},
        )
        assert resp2.status_code == 401

    async def test_logout_without_cookie(self, client: AsyncClient):
        """Logout without a cookie should still succeed (idempotent)."""
        resp = await client.post(f"{AUTH_PREFIX}/logout")
        assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Get current user
# ---------------------------------------------------------------------------


class TestMe:
    async def test_me_success(self, client: AsyncClient, db: AsyncSession):
        login_resp = await _register_and_verify(client, db, "me@example.com")
        access_token = login_resp.json()["access_token"]

        resp = await client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "me@example.com"
        assert body["auth_provider"] == "email"
        assert body["email_verified"] is True
        assert "id" in body
        assert "password_hash" not in body  # Not leaked

    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get(f"{AUTH_PREFIX}/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------


class TestPasswordReset:
    async def test_forgot_password_success(
        self, client: AsyncClient, db: AsyncSession
    ):
        await _register_and_verify(client, db, "reset@example.com")

        resp = await client.post(
            f"{AUTH_PREFIX}/forgot-password",
            json={"email": "reset@example.com"},
        )
        assert resp.status_code == 200

        # Verify a reset token was created
        user_result = await db.execute(
            select(User).where(User.email == "reset@example.com")
        )
        user = user_result.scalar_one()
        token_result = await db.execute(
            select(EmailToken).where(
                EmailToken.user_id == user.id,
                EmailToken.token_type == "password_reset",
            )
        )
        token = token_result.scalar_one()
        assert not token.is_used

    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Should return success even for unknown emails (prevent enumeration)."""
        resp = await client.post(
            f"{AUTH_PREFIX}/forgot-password",
            json={"email": "nobody@example.com"},
        )
        assert resp.status_code == 200

    async def test_reset_password_success(
        self, client: AsyncClient, db: AsyncSession
    ):
        await _register_and_verify(client, db, "fullreset@example.com")

        # Request reset
        await client.post(
            f"{AUTH_PREFIX}/forgot-password",
            json={"email": "fullreset@example.com"},
        )

        # Get the token from DB
        user_result = await db.execute(
            select(User).where(User.email == "fullreset@example.com")
        )
        user = user_result.scalar_one()

        # Create a known reset token
        from app.security import create_url_safe_token, hash_refresh_token
        from datetime import datetime, timedelta, timezone

        raw_token = create_url_safe_token()
        reset_token = EmailToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            token_type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_token)
        await db.flush()

        # Reset password
        resp = await client.post(
            f"{AUTH_PREFIX}/reset-password",
            json={"token": raw_token, "password": "newpassword123"},
        )
        assert resp.status_code == 200
        assert "reset" in resp.json()["message"].lower()

        # Login with new password should work
        login_resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "fullreset@example.com", "password": "newpassword123"},
        )
        assert login_resp.status_code == 200

        # Login with old password should fail
        old_login_resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "fullreset@example.com", "password": "securepass123"},
        )
        assert old_login_resp.status_code == 401

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            f"{AUTH_PREFIX}/reset-password",
            json={"token": "invalid-token", "password": "newpassword123"},
        )
        assert resp.status_code == 400

    async def test_reset_password_revokes_sessions(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Password reset should invalidate all refresh tokens."""
        login_resp = await _register_and_verify(
            client, db, "revoke-sessions@example.com"
        )
        old_refresh = login_resp.cookies.get("refresh_token")

        # Create a known reset token
        from app.security import create_url_safe_token, hash_refresh_token
        from datetime import datetime, timedelta, timezone

        user_result = await db.execute(
            select(User).where(User.email == "revoke-sessions@example.com")
        )
        user = user_result.scalar_one()

        raw_token = create_url_safe_token()
        reset_token = EmailToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            token_type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_token)
        await db.flush()

        # Reset password
        await client.post(
            f"{AUTH_PREFIX}/reset-password",
            json={"token": raw_token, "password": "newpassword123"},
        )

        # Old refresh token should be revoked
        resp = await client.post(
            f"{AUTH_PREFIX}/refresh",
            cookies={"refresh_token": old_refresh},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Account Lockout
# ---------------------------------------------------------------------------


class TestAccountLockout:
    async def test_lockout_after_failed_attempts(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Account should lock after too many failed login attempts."""
        await _register_and_verify(client, db, "lockout@example.com")

        # Override lockout settings for faster testing
        from app.config import settings

        original_attempts = settings.account_lockout_attempts
        settings.account_lockout_attempts = 3

        try:
            # Fail 3 times
            for i in range(3):
                resp = await client.post(
                    f"{AUTH_PREFIX}/login",
                    json={
                        "email": "lockout@example.com",
                        "password": "wrongpassword",
                    },
                )
                assert resp.status_code == 401

            # Verify records exist in db
            from sqlalchemy import func, select as sa_select
            from app.models.failed_login import FailedLoginAttempt

            count_result = await db.execute(
                sa_select(func.count())
                .select_from(FailedLoginAttempt)
                .where(FailedLoginAttempt.email == "lockout@example.com")
            )
            assert count_result.scalar() == 3

            # Next attempt should be locked (423)
            resp = await client.post(
                f"{AUTH_PREFIX}/login",
                json={"email": "lockout@example.com", "password": "securepass123"},
            )
            assert resp.status_code == 423
            assert "locked" in resp.json()["detail"].lower()
        finally:
            settings.account_lockout_attempts = original_attempts

    async def test_successful_login_clears_failed_attempts(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Successful login should clear failed attempt counter."""
        await _register_and_verify(client, db, "clearlock@example.com")

        # Fail twice
        for _ in range(2):
            await client.post(
                f"{AUTH_PREFIX}/login",
                json={"email": "clearlock@example.com", "password": "wrong"},
            )

        # Successful login
        resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "clearlock@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 200

        # Fail twice more — should NOT be locked (counter was cleared)
        for _ in range(2):
            await client.post(
                f"{AUTH_PREFIX}/login",
                json={"email": "clearlock@example.com", "password": "wrong"},
            )

        # Should still be able to attempt (not locked out)
        resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "clearlock@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 200
