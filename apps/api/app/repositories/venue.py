"""Venue and court data access."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.venue import Venue, VenueAvailability, VenueCourt
from app.repositories.base import BaseRepository


class VenueRepository(BaseRepository[Venue]):
    model = Venue

    def get(self, entity_id: uuid.UUID) -> Venue | None:
        return self.db.get(Venue, entity_id)

    def list(
        self,
        *,
        city: str | None = None,
        category: str | None = None,
        owner_id: uuid.UUID | None = None,
        search: str | None = None,
        include_inactive: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Venue], int]:
        stmt = select(Venue)
        if not include_inactive:
            stmt = stmt.where(Venue.is_active.is_(True))
        if city is not None:
            stmt = stmt.where(Venue.city == city)
        if category is not None:
            stmt = stmt.where(Venue.category == category)
        if owner_id is not None:
            stmt = stmt.where(Venue.owner_id == owner_id)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Venue.name.ilike(like))
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(Venue.name.asc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def court_count(self, venue_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(VenueCourt)
                .where(VenueCourt.venue_id == venue_id)
            )
            or 0
        )

    def list_courts(self, venue_id: uuid.UUID) -> Sequence[VenueCourt]:
        return self.db.scalars(
            select(VenueCourt)
            .where(VenueCourt.venue_id == venue_id)
            .order_by(VenueCourt.name.asc())
        ).all()

    def list_courts_with_availability(self, venue_id: uuid.UUID) -> Sequence[VenueCourt]:
        """Resources for a venue with their weekly windows eagerly loaded."""
        return self.db.scalars(
            select(VenueCourt)
            .where(VenueCourt.venue_id == venue_id)
            .options(selectinload(VenueCourt.availability))
            .order_by(VenueCourt.name.asc())
        ).all()

    def availability_for_courts(
        self, court_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, list[VenueAvailability]]:
        """All weekly windows for ``court_ids``, grouped by court id."""
        if not court_ids:
            return {}
        rows = self.db.scalars(
            select(VenueAvailability)
            .where(VenueAvailability.court_id.in_(court_ids))
            .order_by(
                VenueAvailability.weekday.asc(), VenueAvailability.opens_at.asc()
            )
        ).all()
        grouped: dict[uuid.UUID, list[VenueAvailability]] = {}
        for window in rows:
            grouped.setdefault(window.court_id, []).append(window)
        return grouped

    def get_court(self, court_id: uuid.UUID) -> VenueCourt | None:
        return self.db.get(VenueCourt, court_id)

    def add_court(self, court: VenueCourt) -> VenueCourt:
        self.db.add(court)
        self.db.flush()
        return court

    def add_availability(self, window: VenueAvailability) -> VenueAvailability:
        self.db.add(window)
        self.db.flush()
        return window
