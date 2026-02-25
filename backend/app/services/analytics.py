"""Service layer for analytics operations."""

import hashlib
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.landing_pageview import LandingPageview


async def record_pageview(
    db: AsyncSession,
    page_url: str,
    referrer: str | None,
    user_agent: str | None,
    session_id: str | None,
    client_ip: str | None,
) -> None:
    """Record a landing page pageview."""
    ip_hash = None
    if client_ip:
        daily_salt = f"mf-{date.today().isoformat()}"
        ip_hash = hashlib.sha256(
            f"{client_ip}:{daily_salt}".encode()
        ).hexdigest()[:16]

    pageview = LandingPageview(
        page_url=page_url,
        referrer=referrer,
        user_agent=user_agent,
        session_id=session_id,
        ip_hash=ip_hash,
    )
    db.add(pageview)
