"""Follow model: a directed follower -> following edge between two users."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Follow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One row per directed follow edge (follower_id follows following_id).

    The unique constraint makes following idempotent at the database level.
    """

    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint(
            "follower_id", "following_id", name="uq_follows_follower_following"
        ),
    )

    follower_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
