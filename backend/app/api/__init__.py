"""API routers for MealFrame application."""

from .today import router as today_router
from .weekly import router as weekly_router

__all__ = ["today_router", "weekly_router"]
