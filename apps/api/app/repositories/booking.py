"""Booking data access."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.booking import Booking
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    model = Booking

    def get(self, entity_id: uuid.UUID) -> Booking | None:
        return self.db.get(Booking, entity_id)

    def get_by_idempotency_key(self, key: str) -> Booking | None:
        return self.db.scalar(select(Booking).where(Booking.idempotency_key == key))

    def list(
        self,
        *,
        booked_by_id: uuid.UUID | None = None,
        venue_court_id: uuid.UUID | None = None,
        activity_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Booking], int]:
        stmt = select(Booking)
        if booked_by_id is not None:
            stmt = stmt.where(Booking.booked_by_id == booked_by_id)
        if venue_court_id is not None:
            stmt = stmt.where(Booking.venue_court_id == venue_court_id)
        if activity_id is not None:
            stmt = stmt.where(Booking.activity_id == activity_id)
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(Booking.starts_at.desc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def overlapping(
        self,
        court_id: uuid.UUID,
        starts_at: object,
        ends_at: object,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> Sequence[Booking]:
        stmt = select(Booking).where(
            Booking.venue_court_id == court_id,
            Booking.status.in_(("pending", "confirmed")),
            Booking.starts_at < ends_at,
            Booking.ends_at > starts_at,
        )
        if exclude_id is not None:
            stmt = stmt.where(Booking.id != exclude_id)
        return self.db.scalars(stmt).all()
