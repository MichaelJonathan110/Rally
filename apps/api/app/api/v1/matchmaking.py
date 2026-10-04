"""Matchmaking recommendation endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.schemas.discovery import MatchmakingResponse
from app.services.matchmaking_service import MatchmakingService

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/recommendations", response_model=MatchmakingResponse)
def recommendations(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> MatchmakingResponse:
    """Personalised activity + partner recommendations for the caller."""
    return MatchmakingService(db).recommend(current_user.id, limit=limit)
