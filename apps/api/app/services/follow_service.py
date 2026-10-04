"""Follow / friends business logic.

The follow graph is a simple directed edge table (``follows``). A *friend* is a
mutual follow (both directions exist). Reads never invent data: a user's rating
is only surfaced when they have a verified match (``games_played >= 1``).
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.follow import Follow
from app.models.rating import MmrRating
from app.models.user import User
from app.schemas.follow import FollowCounts, UserSummary


class FollowService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- mutations ---------------------------------------------------------
    def follow(self, actor_id: uuid.UUID, target_id: uuid.UUID) -> None:
        if self.db.get(User, target_id) is None:
            raise NotFoundError("User not found")
        if actor_id == target_id:
            raise ValidationError("You cannot follow yourself")
        if self.is_following(actor_id, target_id):
            return
        self.db.add(Follow(follower_id=actor_id, following_id=target_id))
        self.db.commit()

    def unfollow(self, actor_id: uuid.UUID, target_id: uuid.UUID) -> None:
        edge = self.db.scalar(
            select(Follow).where(
                Follow.follower_id == actor_id, Follow.following_id == target_id
            )
        )
        if edge is None:
            return
        self.db.delete(edge)
        self.db.commit()

    # -- predicates --------------------------------------------------------
    def is_following(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        return (
            self.db.scalar(
                select(Follow.id).where(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id,
                )
            )
            is not None
        )

    # -- collections -------------------------------------------------------
    def followers(self, user_id: uuid.UUID) -> list[User]:
        stmt = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def following(self, user_id: uuid.UUID) -> list[User]:
        stmt = (
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def friends(self, user_id: uuid.UUID) -> list[User]:
        """Users with a mutual follow (both edges exist)."""
        mine = select(Follow.following_id).where(Follow.follower_id == user_id)
        stmt = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id, Follow.follower_id.in_(mine))
            .order_by(Follow.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def counts(self, user_id: uuid.UUID) -> FollowCounts:
        followers = int(
            self.db.scalar(
                select(func.count())
                .select_from(Follow)
                .where(Follow.following_id == user_id)
            )
            or 0
        )
        following = int(
            self.db.scalar(
                select(func.count())
                .select_from(Follow)
                .where(Follow.follower_id == user_id)
            )
            or 0
        )
        friends = int(
            self.db.scalar(
                select(func.count())
                .select_from(Follow)
                .where(
                    Follow.following_id == user_id,
                    Follow.follower_id.in_(
                        select(Follow.following_id).where(
                            Follow.follower_id == user_id
                        )
                    ),
                )
            )
            or 0
        )
        return FollowCounts(followers=followers, following=following, friends=friends)

    def suggestions(self, user_id: uuid.UUID, limit: int = 8) -> list[User]:
        """Suggest users to follow.

        Excludes self and already-followed users, then prefers (in order): same
        profile city, a shared MMR category, and finally most recent sign-ups.
        """
        followed = select(Follow.following_id).where(Follow.follower_id == user_id)
        me = self.db.get(User, user_id)
        my_city = me.profile.city if me is not None and me.profile is not None else None
        my_categories = set(
            self.db.scalars(
                select(MmrRating.category).where(MmrRating.user_id == user_id)
            ).all()
        )

        stmt = select(User).where(User.id != user_id, User.id.notin_(followed))
        candidates = list(self.db.scalars(stmt).all())

        def rank(user: User) -> tuple[int, int, float]:
            city = user.profile.city if user.profile is not None else None
            same_city = 0 if (my_city and city == my_city) else 1
            shared = 1
            if my_categories:
                user_cats = set(
                    self.db.scalars(
                        select(MmrRating.category).where(MmrRating.user_id == user.id)
                    ).all()
                )
                if user_cats.intersection(my_categories):
                    shared = 0
            else:
                shared = 0
            recency = -(user.created_at.timestamp() if user.created_at else 0.0)
            return (same_city, shared, recency)

        candidates.sort(key=rank)
        return candidates[:limit]

    # -- presentation ------------------------------------------------------
    def to_summary(
        self, user: User, *, viewer_id: uuid.UUID | None = None
    ) -> UserSummary:
        profile = user.profile
        rating_row = self.db.scalar(
            select(MmrRating)
            .where(MmrRating.user_id == user.id)
            .order_by(MmrRating.games_played.desc(), MmrRating.rating.desc())
        )
        games_played = int(
            self.db.scalar(
                select(func.coalesce(func.sum(MmrRating.games_played), 0)).where(
                    MmrRating.user_id == user.id
                )
            )
            or 0
        )
        ranked = rating_row is not None and rating_row.games_played >= 1
        is_following = False
        is_friend = False
        if viewer_id is not None and viewer_id != user.id:
            is_following = self.is_following(viewer_id, user.id)
            is_friend = is_following and self.is_following(user.id, viewer_id)
        return UserSummary(
            user_id=user.id,
            username=user.username,
            display_name=profile.display_name if profile else user.username,
            city=profile.city if profile else None,
            avatar_url=profile.avatar_url if profile else None,
            category=rating_row.category if rating_row is not None else None,
            rating=float(rating_row.rating) if ranked else None,
            games_played=games_played,
            is_following=is_following,
            is_friend=is_friend,
        )

    def summaries(
        self, users: list[User], *, viewer_id: uuid.UUID | None = None
    ) -> list[UserSummary]:
        return [self.to_summary(u, viewer_id=viewer_id) for u in users]
