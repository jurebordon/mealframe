"""
Integration tests for authentication endpoints (ADR-014).

Tests cover:
- POST /api/v1/auth/register — create account, get tokens
- POST /api/v1/auth/login — authenticate, get tokens
- POST /api/v1/auth/refresh — rotate refresh token
- POST /api/v1/auth/logout — revoke refresh token
- GET /api/v1/auth/me — get current user profile
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app
from app.security import hash_password


AUTH_PREFIX = "/api/v1/auth"


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Create an async HTTP client with database override."""

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


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
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        # Refresh token set in cookie
        assert "refresh_token" in resp.cookies

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


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        # Register first
        await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "login@example.com", "password": "securepass123"},
        )

        resp = await client.post(
            f"{AUTH_PREFIX}/login",
            json={"email": "login@example.com", "password": "securepass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in resp.cookies

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "wrong@example.com", "password": "securepass123"},
        )

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
    async def test_refresh_success(self, client: AsyncClient):
        # Register to get tokens
        reg_resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "refresh@example.com", "password": "securepass123"},
        )
        refresh_cookie = reg_resp.cookies.get("refresh_token")
        assert refresh_cookie is not None

        # Use refresh token to get new access token
        resp = await client.post(
            f"{AUTH_PREFIX}/refresh",
            cookies={"refresh_token": refresh_cookie},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        # New refresh token cookie set
        assert "refresh_token" in resp.cookies

    async def test_refresh_reuse_revoked_token(self, client: AsyncClient):
        """After refresh, the old refresh token should be revoked."""
        reg_resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "reuse@example.com", "password": "securepass123"},
        )
        old_refresh = reg_resp.cookies.get("refresh_token")

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
    async def test_logout_clears_cookie(self, client: AsyncClient):
        reg_resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "logout@example.com", "password": "securepass123"},
        )
        refresh_cookie = reg_resp.cookies.get("refresh_token")

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
    async def test_me_success(self, client: AsyncClient):
        reg_resp = await client.post(
            f"{AUTH_PREFIX}/register",
            json={"email": "me@example.com", "password": "securepass123"},
        )
        access_token = reg_resp.json()["access_token"]

        resp = await client.get(
            f"{AUTH_PREFIX}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "me@example.com"
        assert body["auth_provider"] == "email"
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
