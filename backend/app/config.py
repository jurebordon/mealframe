"""
Application configuration.
TODO: Implement in next session.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    database_url: str = "postgresql+asyncpg://mealframe:password@db:5432/mealframe"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
