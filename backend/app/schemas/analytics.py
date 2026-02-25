"""Pydantic schemas for analytics endpoints."""

from pydantic import BaseModel, Field


class PageviewCreate(BaseModel):
    """Request body for recording a pageview."""

    page_url: str = Field(..., max_length=2048)
    referrer: str | None = Field(None, max_length=2048)
    session_id: str | None = Field(None, max_length=64)


class PageviewResponse(BaseModel):
    """Response confirming pageview was recorded."""

    status: str = "ok"
