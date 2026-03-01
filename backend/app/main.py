"""
FastAPI application entry point.

This module creates and configures the FastAPI application instance,
including middleware, lifecycle events, and route registration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import close_db, init_db
from app.api import (
    today_router,
    weekly_router,
    day_templates_router,
    meals_router,
    meal_types_router,
    week_plans_router,
    stats_router,
    analytics_router,
    auth_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database connection
    - Shutdown: Close database connection pool
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
)

# Rate limit error handler (slowapi)
from app.api.auth import limiter  # noqa: E402

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(today_router)
app.include_router(weekly_router)
app.include_router(day_templates_router)
app.include_router(meals_router)
app.include_router(meal_types_router)
app.include_router(week_plans_router)
app.include_router(stats_router)
app.include_router(analytics_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    """
    Health check endpoint.

    Returns:
        dict: Status and message indicating the API is operational
    """
    return {"status": "ok", "message": "MealFrame API"}


@app.get("/health")
async def health():
    """
    Detailed health check endpoint.

    Returns:
        dict: Health status with API version
    """
    return {
        "status": "healthy",
        "version": settings.api_version,
        "service": "mealframe-api",
    }
