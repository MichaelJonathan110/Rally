"""Match results, verification, leaderboard and rating endpoints.

RBAC is enforced here and in :class:`MatchService` - the host is the only user
who may record a match, and only listed participants may verify a result.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import NotFoundError
from app.core.sport_fields import (
    is_known_sport,
    sport_category_slug,
)
from app.models.activity import Activity
from app.schemas.match import (
    LeaderboardEntryRead,
    MatchCreate,
    MatchRead,
    MatchResultRead,
    ResultSubmit,
    SportLeaderboardRead,
    StandingRead,
    UserRatingsRead,
    VerifyRequest,
)
from app.services.activity_service import ActivityService
from app.services.match_service import MatchService
from app.services.mmr_service import MmrService

router = APIRouter(tags=["matches"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/activities/{activity_id}/matches",
    response_model=MatchRead,
    status_code=status.HTTP_201_CREATED,
)
def create_match(
    activity_id: uuid.UUID,
    payload: MatchCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> MatchRead:
    """Record a match on an activity (host only)."""
    match = MatchService(db).create_match(
        activity_id,
        current_user.id,
        [p.model_dump() for p in payload.participants],
        scheduled_at=payload.scheduled_at,
    )
    return MatchRead.model_validate(match)


@router.get("/matches/{match_id}", response_model=MatchRead)
def get_match(match_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> MatchRead:
    """Fetch a match with its participants and results."""
    return MatchRead.model_validate(MatchService(db).get(match_id))


@router.post(
    "/matches/{match_id}/result",
    response_model=MatchResultRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_result(
    match_id: uuid.UUID,
    payload: ResultSubmit,
    current_user: CurrentUser,
    db: DbSession,
) -> MatchResultRead:
    """Submit a final score; the result is PENDING_VERIFICATION."""
    result = MatchService(db).submit_result(
        match_id,
        current_user.id,
        team_a_score=payload.team_a_score,
        team_b_score=payload.team_b_score,
        notes=payload.notes,
    )
    return MatchResultRead.model_validate(result)


@router.post("/matches/{match_id}/verify", response_model=MatchResultRead)
def verify_result(
    match_id: uuid.UUID,
    payload: VerifyRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> MatchResultRead:
    """Confirm or dispute a submitted result (listed participants only).

    Once a majority confirm, MMR is applied and the result becomes VERIFIED.
    """
    result = MatchService(db).verify_result(
        match_id,
        payload.result_id,
        current_user.id,
        confirmed=payload.confirmed,
        comment=payload.comment,
    )
    return MatchResultRead.model_validate(result)


@router.get(
    "/activities/{activity_id}/leaderboard",
    response_model=list[LeaderboardEntryRead],
)
def get_leaderboard(
    activity_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    period: str = Query(default="all_time"),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[LeaderboardEntryRead]:
    """Ranked MMR leaderboard for the activity's sport (sport-scoped)."""
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise NotFoundError("Activity not found")
    sport_slug = activity.sport_slug
    category = (
        sport_category_slug(str(sport_slug)) if sport_slug else str(activity.category)
    )
    entries = MmrService(db).get_leaderboard(sport_slug, category, period, limit)
    return [LeaderboardEntryRead.model_validate(e) for e in entries]


@router.get(
    "/sports/{sport_slug}/leaderboard",
    response_model=SportLeaderboardRead,
)
def get_sport_leaderboard(
    sport_slug: str,
    current_user: CurrentUser,
    db: DbSession,
    period: str = Query(default="all_time"),
    limit: int = Query(default=50, ge=1, le=100),
) -> SportLeaderboardRead:
    """Per-sport MMR leaderboard with the caller's own standing.

    Entries are ordered by rating; the caller gets an **UNRANKED** standing when
    they have no verified matches in this sport.
    """
    if not is_known_sport(sport_slug):
        raise NotFoundError("Sport not found")
    category = sport_category_slug(sport_slug)
    service = MmrService(db)
    entries = service.get_leaderboard(sport_slug, category, period, limit)
    standing = service.get_standing(current_user.id, sport_slug, category, period)
    return SportLeaderboardRead(
        sport_slug=sport_slug,
        period=period,
        entries=[LeaderboardEntryRead.model_validate(e) for e in entries],
        me=StandingRead.model_validate(standing),
    )


@router.get("/users/{user_id}/ratings", response_model=UserRatingsRead)
def get_user_ratings(
    user_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> UserRatingsRead:
    """A user's per-category MMR ratings plus recent history."""
    service = MmrService(db)
    ratings = service.get_user_ratings(user_id)
    history = service.history_for_user(user_id)
    return UserRatingsRead(
        user_id=user_id,
        ratings=[r for r in ratings],
        history=[h for h in history],
    )
