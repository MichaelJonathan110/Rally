"""Tournament, TournamentEntry and TournamentMatch models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from app.models.enums import (
    ActivityCategory,
    TournamentFormat,
    TournamentStatus,
    pg_enum,
)


class Tournament(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tournaments"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_tournaments_slug"),
        CheckConstraint("max_entries > 0", name="ck_tournaments_max_entries"),
    )

    organizer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    venue_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("venues.id", ondelete="SET NULL"), index=True
    )
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[ActivityCategory] = mapped_column(
        pg_enum(ActivityCategory, "activitycategory"), nullable=False, index=True
    )
    format: Mapped[TournamentFormat] = mapped_column(
        pg_enum(TournamentFormat, "tournamentformat"),
        default=TournamentFormat.SINGLE_ELIMINATION,
        nullable=False,
    )
    status: Mapped[TournamentStatus] = mapped_column(
        pg_enum(TournamentStatus, "tournamentstatus"),
        default=TournamentStatus.DRAFT,
        nullable=False,
        index=True,
    )
    max_entries: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    entry_fee_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    entries: Mapped[list[TournamentEntry]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )


class TournamentEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tournament_entries"
    __table_args__ = (
        UniqueConstraint("tournament_id", "user_id", name="uq_tournament_entries_tournament_user"),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seed: Mapped[int | None] = mapped_column(Integer)
    eliminated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    final_placement: Mapped[int | None] = mapped_column(Integer)

    tournament: Mapped[Tournament] = relationship(back_populates="entries")


class TournamentMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A bracket fixture linking a tournament to a played ``matches`` row."""

    __tablename__ = "tournament_matches"
    __table_args__ = (
        UniqueConstraint(
            "tournament_id", "round_number", "slot", name="uq_tournament_matches_slot"
        ),
        CheckConstraint("round_number >= 1", name="ck_tournament_matches_round"),
    )

    tournament_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL"), index=True
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    home_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tournament_entries.id", ondelete="SET NULL")
    )
    away_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tournament_entries.id", ondelete="SET NULL")
    )
    # Winner of this fixture. NULL until a result is recorded. Advancing the
    # bracket writes the winner into the next round's home/away slot.
    winner_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tournament_entries.id", ondelete="SET NULL")
    )
