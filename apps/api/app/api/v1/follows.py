"""Follow / friends endpoints: follow, unfollow and social graph reads."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.schemas.follow import FollowCounts, FollowList
from app.services.follow_service import FollowService

router = APIRouter(tags=["follows"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/me/following", response_model=FollowList)
def my_following(current_user: CurrentUser, db: DbSession) -> FollowList:
    service = FollowService(db)
    users = service.following(current_user.id)
    items = service.summaries(users, viewer_id=current_user.id)
    return FollowList(items=items, total=len(items))


@router.get("/me/friends", response_model=FollowList)
def my_friends(current_user: CurrentUser, db: DbSession) -> FollowList:
    service = FollowService(db)
    users = service.friends(current_user.id)
    items = service.summaries(users, viewer_id=current_user.id)
    return FollowList(items=items, total=len(items))


@router.get("/me/follow-suggestions", response_model=FollowList)
def my_follow_suggestions(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> FollowList:
    service = FollowService(db)
    users = service.suggestions(current_user.id, limit=limit)
    items = service.summaries(users, viewer_id=current_user.id)
    return FollowList(items=items, total=len(items))


@router.post("/users/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def follow_user(user_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    FollowService(db).follow(current_user.id, user_id)


@router.delete("/users/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(user_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    FollowService(db).unfollow(current_user.id, user_id)


@router.get("/users/{user_id}/followers", response_model=FollowList)
def list_followers(user_id: uuid.UUID, db: DbSession) -> FollowList:
    service = FollowService(db)
    users = service.followers(user_id)
    return FollowList(items=service.summaries(users), total=len(users))


@router.get("/users/{user_id}/following", response_model=FollowList)
def list_following(user_id: uuid.UUID, db: DbSession) -> FollowList:
    service = FollowService(db)
    users = service.following(user_id)
    return FollowList(items=service.summaries(users), total=len(users))


@router.get("/users/{user_id}/friends", response_model=FollowList)
def list_friends(user_id: uuid.UUID, db: DbSession) -> FollowList:
    service = FollowService(db)
    users = service.friends(user_id)
    return FollowList(items=service.summaries(users), total=len(users))


@router.get("/users/{user_id}/follow-counts", response_model=FollowCounts)
def follow_counts(user_id: uuid.UUID, db: DbSession) -> FollowCounts:
    return FollowService(db).counts(user_id)
