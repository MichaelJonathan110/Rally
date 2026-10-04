"""MMR rating, immutable history and leaderboard models.

MMR is **sport-specific** (a player has one rating per sport slug), Elo-style and transactional. ``mmr_history`` is
append-only: corrections are new rows, never updates. MMR is never accepted as
client input; it is computed server-side from verified results and applied
idempotently per verified match.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MmrRating(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Current MMR for a (user, sport) pair.

    ``sport_slug`` is the scope key - one row per (user, sport). ``category`` is
    retained for backward compatibility and holds the sport's catalog category
    (racket/team/combat/...); legacy rows without a sport keep their activity
    category and use a ``category:<cat>`` scope key.
    """

    __tablename__ = "mmr_ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "sport_slug", name="uq_mmr_ratings_user_sport"),
        CheckConstraint("rating >= 0", name="ck_mmr_ratings_rating"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    #: Scope key: the sport slug (or ``category:<cat>`` for legacy, sport-less rows).
    sport_slug: Mapped[str] = mapped_column(
        String(60), nullable=False, index=True, default="legacy"
    )
    rating: Mapped[float] = mapped_column(Numeric(10, 2), default=1200.0, nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    history: Mapped[list[MmrHistory]] = relationship(
        back_populates="rating", cascade="all, delete-orphan"
    )


class MmrHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable, append-only MMR change record (never updated in place)."""

    __tablename__ = "mmr_history"
    __table_args__ = (
        # Idempotency is per (result, user): a team result writes one row per
        # member, so the constraint must be composite (not match_result_id alone).
        UniqueConstraint(
            "match_result_id", "user_id", name="uq_mmr_history_result_user"
        ),
    )

    rating_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("mmr_ratings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_result_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="SET NULL"),
        index=True,
        comment="Idempotency key: one MMR delta per verified result",
    )
    rating_before: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    rating_after: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    delta: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(80), default="match", nullable=False)

    rating: Mapped[MmrRating] = relationship(back_populates="history")


class LeaderboardEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A materialised leaderboard row for a sport + period."""

    __tablename__ = "leaderboard_entries"
    __table_args__ = (
        UniqueConstraint(
            "sport_slug", "period", "user_id", name="uq_leaderboard_entries_sport_period_user"
        ),
        CheckConstraint("rank >= 1", name="ck_leaderboard_entries_rank"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    #: Scope key: the sport slug (or ``category:<cat>`` for legacy, sport-less rows).
    sport_slug: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), default="all_time", nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
