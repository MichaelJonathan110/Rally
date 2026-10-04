"""Venue endpoints: CRUD (owner-only writes) and court/resource management.

The venue payload is sport-aware: it exposes the REAL primary name, the city
secondary line, the supported sport slugs, the typed resources (venue_kind +
resource_label) and a per-resource availability summary.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.models.enums import ActivityCategory, ReviewTargetType
from app.schemas.common import Page
from app.schemas.moderation import ReviewCreate, ReviewRead, VenueRatingSummary
from app.schemas.venue import (
    VenueAvailabilitySummary,
    VenueCourtCreate,
    VenueCourtRead,
    VenueCreate,
    VenueRead,
    VenueResourceRead,
    VenueUpdate,
)
from app.services.moderation_service import ReviewService
from app.services.venue_service import VenueService

router = APIRouter(prefix="/venues", tags=["venues"])

DbSession = Annotated[Session, Depends(get_db)]


def _to_read(service: VenueService, venue: object) -> VenueRead:
    data = VenueRead.model_validate(venue)
    venue_id = venue.id  # type: ignore[attr-defined]
    data.court_count = service.court_count(venue_id)
    data.location = service.city_secondary(venue)  # type: ignore[arg-type]
    data.sport_slugs = service.sport_slugs(venue)  # type: ignore[arg-type]
    data.venue_kind = service.venue_kind(venue)  # type: ignore[arg-type]
    data.resources = [
        VenueResourceRead(
            id=resource["id"],
            name=resource["name"],
            kind=resource["kind"],
            label=resource["label"],
            availability=resource["availability"],
        )
        for resource in service.resources(venue_id)
    ]
    data.availability = VenueAvailabilitySummary(**service.availability_summary(venue_id))
    return data


@router.get("", response_model=Page[VenueRead])
def list_venues(
    db: DbSession,
    city: Annotated[str | None, Query(max_length=120)] = None,
    category: Annotated[ActivityCategory | None, Query()] = None,
    owner_id: Annotated[uuid.UUID | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    include_inactive: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[VenueRead]:
    service = VenueService(db)
    rows, total = service.list_venues(
        city=city,
        category=category.value if category else None,
        owner_id=owner_id,
        search=search,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    return Page[VenueRead](
        items=[_to_read(service, v) for v in rows], total=total, limit=limit, offset=offset
    )


@router.post("", response_model=VenueRead, status_code=status.HTTP_201_CREATED)
def create_venue(
    payload: VenueCreate, current_user: CurrentUser, db: DbSession
) -> VenueRead:
    """Create a venue (optionally with resources + availability). Caller is owner."""
    service = VenueService(db)
    venue = service.create(current_user.id, payload.model_dump())
    return _to_read(service, venue)


@router.get("/{venue_id}", response_model=VenueRead)
def get_venue(venue_id: uuid.UUID, db: DbSession) -> VenueRead:
    service = VenueService(db)
    return _to_read(service, service.get(venue_id))


@router.patch("/{venue_id}", response_model=VenueRead)
def update_venue(
    venue_id: uuid.UUID,
    payload: VenueUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> VenueRead:
    """Owner-only partial update."""
    service = VenueService(db)
    venue = service.update(venue_id, current_user.id, payload.model_dump(exclude_unset=True))
    return _to_read(service, venue)


@router.get("/{venue_id}/resources", response_model=list[VenueResourceRead])
def list_resources(venue_id: uuid.UUID, db: DbSession) -> list[VenueResourceRead]:
    """The venue's bookable resources, each typed by venue_kind + availability."""
    service = VenueService(db)
    service.get(venue_id)  # 404 if the venue does not exist
    return [
        VenueResourceRead(
            id=resource["id"],
            name=resource["name"],
            kind=resource["kind"],
            label=resource["label"],
            availability=resource["availability"],
        )
        for resource in service.resources(venue_id)
    ]


@router.get("/{venue_id}/availability", response_model=VenueAvailabilitySummary)
def availability_summary(venue_id: uuid.UUID, db: DbSession) -> VenueAvailabilitySummary:
    """Per-resource availability roll-up for a venue."""
    service = VenueService(db)
    service.get(venue_id)  # 404 if the venue does not exist
    return VenueAvailabilitySummary(**service.availability_summary(venue_id))


@router.get("/{venue_id}/courts", response_model=list[VenueCourtRead])
def list_courts(venue_id: uuid.UUID, db: DbSession) -> list[VenueCourtRead]:
    rows = VenueService(db).list_courts(venue_id)
    return [VenueCourtRead.model_validate(c) for c in rows]


@router.post(
    "/{venue_id}/courts",
    response_model=VenueCourtRead,
    status_code=status.HTTP_201_CREATED,
)
def add_court(
    venue_id: uuid.UUID,
    payload: VenueCourtCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> VenueCourtRead:
    """Owner-only: add a resource (with optional availability windows)."""
    court = VenueService(db).add_court(venue_id, current_user.id, payload.model_dump())
    return VenueCourtRead.model_validate(court)


@router.post(
    "/{venue_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    venue_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ReviewRead:
    """Create a review for a venue. Any authenticated user; one per venue."""
    VenueService(db).get(venue_id)  # 404 if the venue does not exist
    review = ReviewService(db).create(
        current_user.id,
        target_type=ReviewTargetType.VENUE,
        target_id=venue_id,
        rating=payload.rating,
        body=payload.body,
    )
    return ReviewRead.model_validate(review)


@router.get("/{venue_id}/reviews", response_model=VenueRatingSummary)
def list_reviews(venue_id: uuid.UUID, db: DbSession) -> VenueRatingSummary:
    """All reviews for a venue plus an aggregate rating."""
    VenueService(db).get(venue_id)  # 404 if the venue does not exist
    summary = ReviewService(db).summary(ReviewTargetType.VENUE, venue_id)
    return VenueRatingSummary(
        venue_id=venue_id,
        average_rating=summary["average_rating"],
        review_count=summary["review_count"],
        reviews=[ReviewRead.model_validate(r) for r in summary["reviews"]],
    )
