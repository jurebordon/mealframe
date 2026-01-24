"""
FastAPI application entry point.

This module creates and configures the FastAPI application instance,
including middleware, lifecycle events, and route registration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, init_db
from app.api import today_router


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
