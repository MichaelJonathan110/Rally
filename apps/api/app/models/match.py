"""Match, MatchParticipant, MatchResult and ResultVerification models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import MatchResultStatus, MatchStatus, pg_enum


class Match(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matches"

    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("activities.id", ondelete="SET NULL"), index=True
    )
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tournaments.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[MatchStatus] = mapped_column(
        pg_enum(MatchStatus, "matchstatus"),
        default=MatchStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    participants: Mapped[list[MatchParticipant]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )
    results: Mapped[list[MatchResult]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


class MatchParticipant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "match_participants"
    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_participants_match_user"),
    )

    match_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_winner: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    match: Mapped[Match] = relationship(back_populates="participants")


class MatchResult(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "match_results"

    match_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_by_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[MatchResultStatus] = mapped_column(
        pg_enum(MatchResultStatus, "matchresultstatus"),
        default=MatchResultStatus.PENDING,
        nullable=False,
        index=True,
    )
    team_a_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    team_b_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winner_team: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    # Idempotency: MMR application keyed off the verified result (never client input).
    mmr_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    match: Mapped[Match] = relationship(back_populates="results")
    verifications: Mapped[list[ResultVerification]] = relationship(
        back_populates="result", cascade="all, delete-orphan"
    )


class ResultVerification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A per-user confirmation/dispute of a submitted match result."""

    __tablename__ = "result_verifications"
    __table_args__ = (
        UniqueConstraint("result_id", "user_id", name="uq_result_verifications_result_user"),
    )

    result_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disputed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))

    result: Mapped[MatchResult] = relationship(back_populates="verifications")
