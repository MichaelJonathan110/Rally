"""System endpoints: liveness/readiness and brand info."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.brand import brand
from app.core.config import settings
from app.db.session import engine

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    db: str


class BrandResponse(BaseModel):
    name: str
    tagline: str
    short_name: str
    domain: str
    support_email: str
    theme: dict[str, str]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe with a real database connectivity check."""
    db_state = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any failure means the DB is down
        db_state = "down"
    return HealthResponse(status="ok", version=settings.VERSION, db=db_state)


@router.get("/brand", response_model=BrandResponse)
def brand_info() -> BrandResponse:
    """Public brand payload (no secrets). Single source of truth."""
    return BrandResponse.model_validate(brand.to_public_dict())
