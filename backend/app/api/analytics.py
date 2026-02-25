"""API routes for lightweight analytics."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.analytics import PageviewCreate, PageviewResponse
from ..services.analytics import record_pageview

router = APIRouter(prefix="/api/v1", tags=["Analytics"])


@router.post(
    "/analytics/pageview",
    response_model=PageviewResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_pageview(
    body: PageviewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PageviewResponse:
    """Record a landing page pageview. Fire-and-forget from the frontend."""
    await record_pageview(
        db=db,
        page_url=body.page_url,
        referrer=body.referrer,
        user_agent=request.headers.get("user-agent"),
        session_id=body.session_id,
        client_ip=request.client.host if request.client else None,
    )
    return PageviewResponse()
