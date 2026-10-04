"""Check-in schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CheckInCreate(BaseModel):
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    method: str = Field(default="manual", min_length=2, max_length=40)


class CheckInRead(ORMModel):
    id: uuid.UUID
    activity_id: uuid.UUID
    user_id: uuid.UUID
    checked_in_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    method: str
