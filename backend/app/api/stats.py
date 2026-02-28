"""
API routes for adherence statistics.

- GET /stats - Adherence statistics for a given period

See Tech Spec section 4.3 for full specification.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User
from ..schemas.stats import StatsResponse
from ..services.stats import get_stats

router = APIRouter(prefix="/api/v1", tags=["Stats"])


@router.get("/stats", response_model=StatsResponse)
async def stats(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StatsResponse:
    """
    Get adherence statistics for the given period.

    Returns overall adherence rate, streak info, status breakdown,
    per-meal-type adherence, and daily data points for charting.

    Query parameters:
    - days: Number of days to look back (1-365, default 30)
    """
    return await get_stats(db, days, user.id)
