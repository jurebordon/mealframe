"""API routers for MealFrame application."""

from .today import router as today_router
from .weekly import router as weekly_router
from .day_templates import router as day_templates_router
from .meals import router as meals_router
from .meal_types import router as meal_types_router
from .week_plans import router as week_plans_router
from .stats import router as stats_router
from .analytics import router as analytics_router
from .auth import router as auth_router

__all__ = [
    "today_router",
    "weekly_router",
    "day_templates_router",
    "meals_router",
    "meal_types_router",
    "week_plans_router",
    "stats_router",
    "analytics_router",
    "auth_router",
]
