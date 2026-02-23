"""Common schemas shared across the API - enums, pagination, etc."""
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from .base import BaseSchema


class CompletionStatus(str, Enum):
    """Valid completion statuses for meal slots (ADR-012).

    Per ADR-012, the revised statuses are:
    - followed: Ate the planned meal as-is
    - equivalent: Changed for an equivalent meal (neutral adherence)
    - skipped: Did not eat this meal
    - deviated: Changed for something off-plan (negative adherence)
    - social: Social event prevented following (own category)
    NULL is also valid (unmarked) but represented as None in Python.
    """

    FOLLOWED = "followed"
    EQUIVALENT = "equivalent"
    SKIPPED = "skipped"
    DEVIATED = "deviated"
    SOCIAL = "social"


class Weekday(int, Enum):
    """Weekday enumeration (0=Monday, 6=Sunday)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


# Weekday name mapping for API responses
WEEKDAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


# Generic type for pagination
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items and pagination info."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class SuccessResponse(BaseSchema):
    """Generic success response for operations that don't return data."""

    success: bool = True
    message: str | None = None


class ErrorDetail(BaseModel):
    """Detail for a single validation error."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response format per Tech Spec section 4.6."""

    error: "ErrorBody"


class ErrorBody(BaseModel):
    """Error body with code, message, and optional details."""

    code: str
    message: str
    details: list[ErrorDetail] | None = None


# Error code constants
class ErrorCode:
    """Standard error codes per Tech Spec section 4.6."""

    VALIDATION_ERROR = "VALIDATION_ERROR"  # 400
    NOT_FOUND = "NOT_FOUND"  # 404
    CONFLICT = "CONFLICT"  # 409
    INTERNAL_ERROR = "INTERNAL_ERROR"  # 500
