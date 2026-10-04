"""Data access for tournaments, entries and bracket fixtures."""
from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.tournament import Tournament, TournamentEntry, TournamentMatch


class TournamentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- tournaments ---------------------------------------------------------
    def get(self, tournament_id: uuid.UUID) -> Tournament | None:
        return self.db.get(Tournament, tournament_id)

    def get_by_slug(self, slug: str) -> Tournament | None:
        return self.db.scalar(select(Tournament).where(Tournament.slug == slug))

    def add(self, tournament: Tournament) -> Tournament:
        self.db.add(tournament)
        self.db.flush()
        return tournament

    def list(
        self,
        *,
        status: str | None = None,
        organizer_id: uuid.UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Tournament], int]:
        stmt = select(Tournament)
        if status is not None:
            stmt = stmt.where(Tournament.status == status)
        if organizer_id is not None:
            stmt = stmt.where(Tournament.organizer_id == organizer_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Tournament.name.ilike(like), Tournament.slug.ilike(like)))
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = self.db.scalars(
            stmt.order_by(Tournament.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return list(rows), total

    # -- entries -------------------------------------------------------------
    def get_entry(self, entry_id: uuid.UUID) -> TournamentEntry | None:
        return self.db.get(TournamentEntry, entry_id)

    def get_entry_for_user(
        self, tournament_id: uuid.UUID, user_id: uuid.UUID
    ) -> TournamentEntry | None:
        return self.db.scalar(
            select(TournamentEntry).where(
                TournamentEntry.tournament_id == tournament_id,
                TournamentEntry.user_id == user_id,
            )
        )

    def list_entries(self, tournament_id: uuid.UUID) -> list[TournamentEntry]:
        return list(
            self.db.scalars(
                select(TournamentEntry)
                .where(TournamentEntry.tournament_id == tournament_id)
                .order_by(TournamentEntry.seed.asc().nulls_last(), TournamentEntry.created_at)
            ).all()
        )

    def add_entry(self, entry: TournamentEntry) -> TournamentEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def delete_entry(self, entry: TournamentEntry) -> None:
        self.db.delete(entry)
        self.db.flush()

    # -- bracket -------------------------------------------------------------
    def list_matches(self, tournament_id: uuid.UUID) -> list[TournamentMatch]:
        return list(
            self.db.scalars(
                select(TournamentMatch)
                .where(TournamentMatch.tournament_id == tournament_id)
                .order_by(TournamentMatch.round_number, TournamentMatch.slot)
            ).all()
        )

    def add_match(self, match: TournamentMatch) -> TournamentMatch:
        self.db.add(match)
        self.db.flush()
        return match

    def delete_matches(self, tournament_id: uuid.UUID) -> None:
        for m in self.list_matches(tournament_id):
            self.db.delete(m)
        self.db.flush()

    # -- transaction ---------------------------------------------------------
    def commit(self) -> None:
        self.db.commit()

    def refresh(self, entity: object) -> None:
        self.db.refresh(entity)
