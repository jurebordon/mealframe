"""Pydantic schemas for MealFrame API requests and responses."""

# Base utilities
from .base import BaseSchema, TimestampMixin

# Common schemas
from .common import (
    CompletionStatus,
    Weekday,
    WEEKDAY_NAMES,
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    ErrorBody,
    ErrorDetail,
    ErrorCode,
)

# MealType schemas
from .meal_type import (
    MealTypeBase,
    MealTypeCreate,
    MealTypeUpdate,
    MealTypeResponse,
    MealTypeCompact,
    MealTypeWithCount,
)

# Meal schemas
from .meal import (
    MealBase,
    MealCreate,
    MealUpdate,
    MealResponse,
    MealCompact,
    MealListItem,
    MealImportRow,
    MealImportWarning,
    MealImportError,
    MealImportSummary,
    MealImportResult,
)

# DayTemplate schemas
from .day_template import (
    DayTemplateSlotBase,
    DayTemplateSlotCreate,
    DayTemplateSlotResponse,
    DayTemplateBase,
    DayTemplateCreate,
    DayTemplateUpdate,
    DayTemplateResponse,
    DayTemplateCompact,
    DayTemplateListItem,
)

# WeekPlan schemas
from .week_plan import (
    WeekPlanDayBase,
    WeekPlanDayCreate,
    WeekPlanDayResponse,
    WeekPlanBase,
    WeekPlanCreate,
    WeekPlanUpdate,
    WeekPlanResponse,
    WeekPlanCompact,
    WeekPlanListItem,
)

# WeeklyPlan (instance) schemas
from .weekly_plan import (
    WeeklyPlanSlotBase,
    WeeklyPlanSlotResponse,
    WeeklyPlanSlotWithNext,
    CompletionSummary,
    WeeklyPlanInstanceDayBase,
    WeeklyPlanInstanceDayResponse,
    WeeklyPlanInstanceResponse,
    WeeklyPlanGenerateRequest,
    SwitchTemplateRequest,
    SetOverrideRequest,
    OverrideResponse,
    CompleteSlotRequest,
    CompleteSlotResponse,
    ReassignSlotRequest,
)

# Today/Yesterday schemas
from .today import (
    TodayStats,
    TodayResponse,
    YesterdayReviewResponse,
)

# Stats schemas
from .stats import (
    DailyAdherence,
    StatusBreakdown,
    MealTypeAdherence,
    OverLimitBreakdown,
    StatsResponse,
    StatsQueryParams,
)

__all__ = [
    # Base
    "BaseSchema",
    "TimestampMixin",
    # Common
    "CompletionStatus",
    "Weekday",
    "WEEKDAY_NAMES",
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    "ErrorBody",
    "ErrorDetail",
    "ErrorCode",
    # MealType
    "MealTypeBase",
    "MealTypeCreate",
    "MealTypeUpdate",
    "MealTypeResponse",
    "MealTypeCompact",
    "MealTypeWithCount",
    # Meal
    "MealBase",
    "MealCreate",
    "MealUpdate",
    "MealResponse",
    "MealCompact",
    "MealListItem",
    "MealImportRow",
    "MealImportWarning",
    "MealImportError",
    "MealImportSummary",
    "MealImportResult",
    # DayTemplate
    "DayTemplateSlotBase",
    "DayTemplateSlotCreate",
    "DayTemplateSlotResponse",
    "DayTemplateBase",
    "DayTemplateCreate",
    "DayTemplateUpdate",
    "DayTemplateResponse",
    "DayTemplateCompact",
    "DayTemplateListItem",
    # WeekPlan
    "WeekPlanDayBase",
    "WeekPlanDayCreate",
    "WeekPlanDayResponse",
    "WeekPlanBase",
    "WeekPlanCreate",
    "WeekPlanUpdate",
    "WeekPlanResponse",
    "WeekPlanCompact",
    "WeekPlanListItem",
    # WeeklyPlan
    "WeeklyPlanSlotBase",
    "WeeklyPlanSlotResponse",
    "WeeklyPlanSlotWithNext",
    "CompletionSummary",
    "WeeklyPlanInstanceDayBase",
    "WeeklyPlanInstanceDayResponse",
    "WeeklyPlanInstanceResponse",
    "WeeklyPlanGenerateRequest",
    "SwitchTemplateRequest",
    "SetOverrideRequest",
    "OverrideResponse",
    "CompleteSlotRequest",
    "CompleteSlotResponse",
    "ReassignSlotRequest",
    # Today
    "TodayStats",
    "TodayResponse",
    "YesterdayReviewResponse",
    # Stats
    "DailyAdherence",
    "StatusBreakdown",
    "MealTypeAdherence",
    "OverLimitBreakdown",
    "StatsResponse",
    "StatsQueryParams",
]
