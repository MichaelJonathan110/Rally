"""User progress / streak endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.discovery import UserProgress
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/{user_id}/streak", response_model=UserProgress)
def user_streak(user_id: uuid.UUID, db: DbSession) -> UserProgress:
    """Public progress roll-up: streaks, counts, weekly + calendar activity."""
    return ProgressService(db).compute(user_id)
