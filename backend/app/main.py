"""
FastAPI application entry point.
TODO: Implement in next session.
"""

from fastapi import FastAPI

app = FastAPI(
    title="MealFrame API",
    description="Meal planning API that eliminates decision fatigue",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "MealFrame API"}
