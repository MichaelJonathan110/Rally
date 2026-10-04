"""User-scoped endpoints (achievements, public profile)."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.sports import SPORT_BY_SLUG
from app.models.enums import SkillLevel
from app.models.rating import MmrRating
from app.models.user import Profile, User
from app.schemas.moderation import AchievementRead, UserAchievementRead
from app.schemas.user import UserRead, UserSportRead, UserUpdate
from app.services.moderation_service import AchievementService

router = APIRouter(prefix="/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/{user_id}/achievements", response_model=list[UserAchievementRead])
def list_achievements(user_id: uuid.UUID, db: DbSession) -> list[UserAchievementRead]:
    """List the achievements a user has earned (public read)."""
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    rows = AchievementService(db).for_user(user_id)
    return [
        UserAchievementRead(
            achievement=AchievementRead.model_validate(row["achievement"]),
            earned_at=row["earned_at"],
        )
        for row in rows
    ]


@router.get("/{user_id}/sports", response_model=list[UserSportRead])
def list_user_sports(user_id: uuid.UUID, db: DbSession) -> list[UserSportRead]:
    """List the sports a user has data in, with real per-sport MMR (public read).

    One entry per sport the user has an ``MmrRating`` row for. Ratings are read
    from the existing ``mmr_ratings`` store (the single source of truth); a row
    with no verified matches is surfaced as UNRANKED (``rating=None``,
    ``ranked=False``) instead of an invented number.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    declared_skill = user.profile.skill_level if user.profile is not None else SkillLevel.ANY

    ratings = db.scalars(
        select(MmrRating)
        .where(MmrRating.user_id == user_id)
        .order_by(MmrRating.sport_slug.asc())
    ).all()

    entries: list[UserSportRead] = []
    for rating in ratings:
        row = SPORT_BY_SLUG.get(rating.sport_slug)
        if row is None:
            # Not a catalog sport (e.g. a legacy ``category:<cat>`` scope key).
            continue
        ranked = rating.games_played >= 1
        entries.append(
            UserSportRead(
                sport_slug=rating.sport_slug,
                label=str(row["label_en"]),
                skill_level=declared_skill,
                matches_played=rating.games_played,
                rating=float(rating.rating) if ranked else None,
                ranked=ranked,
            )
        )
    return entries


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    """Return the authenticated caller's own record."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate, current_user: CurrentUser, db: DbSession
) -> UserRead:
    """Update the caller's own profile (self-service, partial).

    Only the supplied fields change. ``avatar_url`` accepts the URL returned by
    ``POST /api/v1/media/upload`` so a freshly uploaded avatar can be persisted.
    """
    user = db.get(User, current_user.id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if "username" in data:
        user.username = data.pop("username")
    if user.profile is None:
        user.profile = Profile(display_name=user.username)
    for field, value in data.items():
        setattr(user.profile, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)
