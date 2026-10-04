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
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    MIN_PASSWORD_LENGTH: int = 8

    # Auth rate limiting (in-memory token bucket keyed by client IP)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_CAPACITY: int = 10
    RATE_LIMIT_AUTH_REFILL_PER_SEC: float = 0.2

    # Payments
    PAYMENT_PROVIDER: str = "mock"  # mock | stripe
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    MOCK_WEBHOOK_SECRET: str = "mock-webhook-secret"

    # Email / transactional mail
    EMAIL_PROVIDER: str = "outbox"  # outbox | smtp | console
    EMAIL_FROM: str = "RALLY <no-reply@rally.local>"
    FRONTEND_BASE_URL: str = "http://localhost:4173"
    EMAIL_VERIFY_TTL_HOURS: int = 24
    PASSWORD_RESET_TTL_HOURS: int = 1
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = True
    OUTBOX_DIR: str = "var/outbox"

    # Media / uploads
    MEDIA_ROOT: str = "var/media"
    MEDIA_URL_PREFIX: str = "/media"
    MAX_UPLOAD_MB: int = 5

    # Datastores
    DATABASE_URL: str = "postgresql+psycopg://rally:rally@localhost:5432/rally"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Self-refreshing demo activities (see app.services.event_refresh).
    # Disable in test/CI runs so the lifespan never touches a real DB.
    EVENT_REFRESH_ENABLED: bool = True

    # CORS
    CORS_ORIGINS: str = (
        "http://127.0.0.1:4173,http://localhost:4173,"
        "http://127.0.0.1:5173,http://localhost:5173"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
