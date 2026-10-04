"""Follow / friends schemas."""
from __future__ import annotations

import uuid

from app.schemas.common import ORMModel


class UserSummary(ORMModel):
    """Compact public user card used by follow lists."""

    user_id: uuid.UUID
    username: str
    display_name: str
    city: str | None = None
    avatar_url: str | None = None
    category: str | None = None
    rating: float | None = None
    games_played: int = 0
    is_following: bool = False
    is_friend: bool = False


class FollowList(ORMModel):
    items: list[UserSummary]
    total: int


class FollowCounts(ORMModel):
    followers: int
    following: int
    friends: int
