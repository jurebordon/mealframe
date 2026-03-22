"""Google OAuth service — OIDC authorization code flow via authlib."""
import secrets
from urllib.parse import urlencode

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import jwt as authlib_jwt
from authlib.oidc.core import CodeIDToken
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Cached discovery document
_discovery: dict | None = None


def google_oauth_enabled() -> bool:
    """Check if Google OAuth is configured."""
    return bool(settings.google_client_id and settings.google_client_secret)


async def _get_discovery() -> dict:
    """Fetch and cache Google's OIDC discovery document."""
    global _discovery
    if _discovery is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(GOOGLE_DISCOVERY_URL)
            resp.raise_for_status()
            _discovery = resp.json()
    return _discovery


async def build_authorization_url(redirect_uri: str) -> tuple[str, str]:
    """
    Build Google consent screen URL.

    Returns (authorization_url, state) where state is a CSRF token
    that must be verified on callback.
    """
    discovery = await _get_discovery()
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = f"{discovery['authorization_endpoint']}?{urlencode(params)}"
    return url, state


async def exchange_code_for_user_info(
    code: str, redirect_uri: str
) -> dict:
    """
    Exchange authorization code for tokens and extract user info from ID token.

    Returns dict with keys: sub, email, email_verified, name, picture.
    """
    discovery = await _get_discovery()

    client = AsyncOAuth2Client(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
    )
    token = await client.fetch_token(
        discovery["token_endpoint"],
        grant_type="authorization_code",
        code=code,
        redirect_uri=redirect_uri,
    )

    # Fetch Google's public keys for JWT verification
    async with httpx.AsyncClient() as http:
        jwks_resp = await http.get(discovery["jwks_uri"])
        jwks_resp.raise_for_status()
        jwks = jwks_resp.json()

    # Verify and decode the ID token
    id_token = token.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ID token in Google response",
        )

    claims = authlib_jwt.decode(
        id_token,
        jwks,
        claims_cls=CodeIDToken,
        claims_options={
            "iss": {"values": ["https://accounts.google.com"]},
            "aud": {"value": settings.google_client_id},
        },
    )
    claims.validate()

    return {
        "sub": claims["sub"],
        "email": claims["email"],
        "email_verified": claims.get("email_verified", False),
        "name": claims.get("name", ""),
        "picture": claims.get("picture", ""),
    }


async def get_or_create_google_user(
    db: AsyncSession, google_info: dict
) -> User:
    """
    Find or create a user from Google OAuth info.

    - If google_sub matches an existing user → return that user
    - If email matches an existing email/password user → link Google account (auto-link)
    - If new email → create new user with auth_provider="google"
    """
    google_sub = google_info["sub"]
    email = google_info["email"]

    # 1. Check by google_sub (returning Google user)
    result = await db.execute(
        select(User).where(User.google_sub == google_sub)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    # 2. Check by email (auto-link existing email/password user)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        # Link Google account to existing user
        user.google_sub = google_sub
        if not user.email_verified:
            user.email_verified = True  # Google verifies email
        await db.flush()
        return user

    # 3. New user — create with Google provider
    if not google_info.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified",
        )

    user = User(
        email=email,
        password_hash=None,
        auth_provider="google",
        google_sub=google_sub,
        email_verified=True,
    )
    db.add(user)
    await db.flush()
    return user
