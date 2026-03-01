"""SQLAlchemy models for MealFrame application."""

# Import all models for Alembic auto-generation
from .user import User
from .refresh_token import RefreshToken
from .email_token import EmailToken
from .failed_login import FailedLoginAttempt
from .meal_type import MealType
from .meal import Meal
from .meal_to_meal_type import meal_to_meal_type
from .day_template import DayTemplate, DayTemplateSlot
from .week_plan import WeekPlan, WeekPlanDay
from .weekly_plan import WeeklyPlanInstance, WeeklyPlanInstanceDay, WeeklyPlanSlot
from .round_robin import RoundRobinState
from .app_config import AppConfig
from .landing_pageview import LandingPageview

__all__ = [
    "User",
    "RefreshToken",
    "EmailToken",
    "FailedLoginAttempt",
    "MealType",
    "Meal",
    "meal_to_meal_type",
    "DayTemplate",
    "DayTemplateSlot",
    "WeekPlan",
    "WeekPlanDay",
    "WeeklyPlanInstance",
    "WeeklyPlanInstanceDay",
    "WeeklyPlanSlot",
    "RoundRobinState",
    "AppConfig",
    "LandingPageview",
]
