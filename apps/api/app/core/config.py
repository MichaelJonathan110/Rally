"""Application settings (pydantic-settings).

All configuration comes from environment variables so the service runs with
zero configuration in dev while remaining fully configurable in production.
Never commit real secrets - see `.env.example`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    APP_NAME: str = "RALLY API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    VERSION: str = "0.1.0"

    # Brand
    BRAND_NAME: str = "RALLY"
    BRAND_TAGLINE: str = "Find your people. Do more together."

    # Security
    SECRET_KEY: str = Field(
        default="dev-insecure-change-me",
        description="HMAC key for JWT signing. MUST be overridden in production.",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Datastores
    DATABASE_URL: str = "postgresql+psycopg://rally:rally@localhost:5432/rally"
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
