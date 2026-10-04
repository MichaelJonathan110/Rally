"""Venue business logic: create venues with courts + availability, ownership.

Sport-awareness: a venue and each of its resources (VenueCourt) are typed by a
venue_kind (see app.core.sports), and availability is generated and reported per
RESOURCE rather than per venue.
"""
from __future__ import annotations

import uuid
from datetime import time

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.core.venue_catalog import (
    CatalogVenue,
    resource_label_for_kind,
    venue_kind_for_sports,
)
from app.models.venue import Venue, VenueAvailability, VenueCourt
from app.repositories.venue import VenueRepository


class VenueService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = VenueRepository(db)

    def get(self, venue_id: uuid.UUID) -> Venue:
        venue = self.repo.get(venue_id)
        if venue is None:
            raise NotFoundError("Venue not found")
        return venue

    def list_venues(
        self,
        *,
        city: str | None = None,
        category: str | None = None,
        owner_id: uuid.UUID | None = None,
        search: str | None = None,
        include_inactive: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Venue], int]:
        rows, total = self.repo.list(
            city=city,
            category=category,
            owner_id=owner_id,
            search=search,
            include_inactive=include_inactive,
            limit=limit,
            offset=offset,
        )
        return list(rows), total

    def court_count(self, venue_id: uuid.UUID) -> int:
        return self.repo.court_count(venue_id)

    @staticmethod
    def primary_name(venue: Venue) -> str:
        """The REAL primary name shown for the venue."""
        return venue.name

    @staticmethod
    def city_secondary(venue: Venue) -> str:
        """The city secondary line (e.g. Tangerang, Indonesia)."""
        country = venue.country or "Indonesia"
        return f"{venue.city}, {country}"

    def resources(self, venue_id: uuid.UUID) -> list[dict]:
        """The venue bookable resources, each typed by venue_kind."""
        courts = self.repo.list_courts_with_availability(venue_id)
        windows = self.repo.availability_for_courts([c.id for c in courts])
        out: list[dict] = []
        for court in courts:
            rows = windows.get(court.id, [])
            out.append(
                {
                    "id": court.id,
                    "name": court.name,
                    "kind": court.venue_kind,
                    "label": court.resource_label
                    or resource_label_for_kind(court.venue_kind),
                    "availability": rows,
                }
            )
        return out

    def availability_summary(self, venue_id: uuid.UUID) -> dict:
        """Per-resource availability roll-up for a venue."""
        resources = self.resources(venue_id)
        weekdays: set[int] = set()
        opens: list[time] = []
        closes: list[time] = []
        with_windows = 0
        total_windows = 0
        for resource in resources:
            rows = resource["availability"]
            if rows:
                with_windows += 1
            total_windows += len(rows)
            for window in rows:
                if not window.is_active:
                    continue
                weekdays.add(window.weekday)
                opens.append(window.opens_at)
                closes.append(window.closes_at)
        return {
            "resource_count": len(resources),
            "resources_with_windows": with_windows,
            "total_windows": total_windows,
            "open_weekdays": sorted(weekdays),
            "earliest_open": min(opens) if opens else None,
            "latest_close": max(closes) if closes else None,
        }

    def catalog_venue(self, venue: Venue) -> CatalogVenue | None:
        """The sport-aware catalog entry for a venue, if it is a demo venue."""
        from app.core.venue_catalog import VENUE_BY_NAME

        return VENUE_BY_NAME.get(venue.name)

    def sport_slugs(self, venue: Venue) -> list[str]:
        """Sport slugs this venue supports (stored, else from the catalog)."""
        if venue.sport_slugs:
            return list(venue.sport_slugs)
        catalog = self.catalog_venue(venue)
        return list(catalog.sport_slugs) if catalog is not None else []

    def venue_kind(self, venue: Venue) -> str | None:
        """The primary venue_kind this venue serves."""
        if venue.venue_kind:
            return venue.venue_kind
        catalog = self.catalog_venue(venue)
        if catalog is not None:
            return catalog.venue_kind
        return venue_kind_for_sports(self.sport_slugs(venue))

    def create(self, owner_id: uuid.UUID, data: dict) -> Venue:
        courts_data = data.pop("courts", [])
        sport_slugs = data.get("sport_slugs") or []
        if not data.get("venue_kind") and sport_slugs:
            data["venue_kind"] = venue_kind_for_sports(sport_slugs)
        venue = Venue(owner_id=owner_id, **data)
        self.repo.add(venue)
        for court_data in courts_data:
            availability = court_data.pop("availability", [])
            if not court_data.get("venue_kind"):
                court_data["venue_kind"] = venue.venue_kind
            court = VenueCourt(venue_id=venue.id, **court_data)
            self.repo.add_court(court)
            for window in availability:
                self.repo.add_availability(VenueAvailability(court_id=court.id, **window))
        self.repo.commit()
        self.repo.refresh(venue)
        return venue

    def update(self, venue_id: uuid.UUID, actor_id: uuid.UUID, data: dict) -> Venue:
        venue = self.get(venue_id)
        if venue.owner_id != actor_id:
            raise PermissionDeniedError("Only the venue owner may modify this venue")
        for key, value in data.items():
            if value is not None:
                setattr(venue, key, value)
        if venue.venue_kind is None and venue.sport_slugs:
            venue.venue_kind = venue_kind_for_sports(venue.sport_slugs)
        self.repo.commit()
        self.repo.refresh(venue)
        return venue

    def list_courts(self, venue_id: uuid.UUID) -> list[VenueCourt]:
        self.get(venue_id)  # 404 if missing
        return list(self.repo.list_courts(venue_id))

    def add_court(self, venue_id: uuid.UUID, actor_id: uuid.UUID, data: dict) -> VenueCourt:
        venue = self.get(venue_id)
        if venue.owner_id != actor_id:
            raise PermissionDeniedError("Only the venue owner may add courts")
        availability = data.pop("availability", [])
        name = data.get("name")
        if not name:
            raise ValidationError("Court name is required")
        existing = {c.name for c in self.repo.list_courts(venue_id)}
        if name in existing:
            raise ValidationError("A court with that name already exists at this venue")
        if not data.get("venue_kind"):
            data["venue_kind"] = venue.venue_kind
        court = VenueCourt(venue_id=venue_id, **data)
        self.repo.add_court(court)
        for window in availability:
            self.repo.add_availability(VenueAvailability(court_id=court.id, **window))
        self.repo.commit()
        self.repo.refresh(court)
        return court

    def get_court(self, court_id: uuid.UUID) -> VenueCourt:
        court = self.repo.get_court(court_id)
        if court is None:
            raise NotFoundError("Court not found")
        return court
