"""
Application configuration using Pydantic Settings.

Environment variables are loaded from .env file or system environment.
All settings can be overridden via environment variables.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    Environment variables should be prefixed with the setting name in uppercase.
    Example: DATABASE_URL, CORS_ORIGINS
    """

    # Database configuration
    database_url: str = "postgresql+asyncpg://mealframe:password@localhost:5432/mealframe"

    # CORS configuration
    # Can be a comma-separated string or a list
    cors_origins: list[str] | str = ["http://localhost:3000"]

    # API configuration
    api_title: str = "MealFrame API"
    api_description: str = "Meal planning API that eliminates decision fatigue"
    api_version: str = "0.1.0"

    # Server configuration
    debug: bool = False

    # Authentication (ADR-014)
    jwt_secret_key: str = "CHANGE-ME-in-production"  # Override via JWT_SECRET_KEY env var
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    admin_email: str = "admin@mealframe.io"  # Admin user for data migration backfill

    # Email (Resend)
    resend_api_key: str = ""  # Override via RESEND_API_KEY env var
    email_from: str = "MealFrame <noreply@mealframe.io>"
    frontend_url: str = "http://localhost:3000"  # For email links

    # Rate limiting
    login_rate_limit: str = "5/minute"
    register_rate_limit: str = "3/minute"
    password_reset_rate_limit: str = "3/minute"
    account_lockout_attempts: int = 10
    account_lockout_minutes: int = 15

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
