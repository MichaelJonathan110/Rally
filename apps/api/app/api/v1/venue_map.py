"""Venue map endpoint: geolocated venues for the map view."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.venue import Venue, VenueCourt
from app.schemas.discovery import MapVenue, VenueMapBounds, VenueMapResponse

router = APIRouter(prefix="/venues", tags=["venues"])

DbSession = Annotated[Session, Depends(get_db)]

_DEFAULT_BOUNDS = VenueMapBounds(min_lat=-11.0, max_lat=6.0, min_lng=95.0, max_lng=141.0)


@router.get("/map", response_model=VenueMapResponse)
def venue_map(
    db: DbSession,
    category: Annotated[str | None, Query(max_length=60)] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 300,
) -> VenueMapResponse:
    """Venues with coordinates (active only), plus aggregate bounds."""
    stmt = select(Venue).where(
        Venue.is_active.is_(True),
        Venue.latitude.isnot(None),
        Venue.longitude.isnot(None),
    )
    if category is not None:
        stmt = stmt.where(Venue.category == category)
    if city is not None:
        stmt = stmt.where(Venue.city == city)
    stmt = stmt.order_by(Venue.name.asc()).limit(limit)
    rows = list(db.scalars(stmt).all())

    ids = [v.id for v in rows]
    counts: dict[object, int] = {}
    if ids:
        counts = {
            vid: int(cnt)
            for vid, cnt in db.execute(
                select(VenueCourt.venue_id, func.count())
                .where(VenueCourt.venue_id.in_(ids))
                .group_by(VenueCourt.venue_id)
            ).all()
        }

    venues: list[MapVenue] = []
    lats: list[float] = []
    lngs: list[float] = []
    for venue in rows:
        lat = float(venue.latitude)  # type: ignore[arg-type]
        lng = float(venue.longitude)  # type: ignore[arg-type]
        lats.append(lat)
        lngs.append(lng)
        venues.append(
            MapVenue(
                id=venue.id,
                name=venue.name,
                city=venue.city,
                province=venue.province,
                area=venue.area,
                category=str(venue.category) if venue.category is not None else None,
                venue_kind=venue.venue_kind,
                latitude=lat,
                longitude=lng,
                court_count=counts.get(venue.id, 0),
                sport_slugs=list(venue.sport_slugs or []),
            )
        )

    bounds = (
        VenueMapBounds(
            min_lat=min(lats), max_lat=max(lats), min_lng=min(lngs), max_lng=max(lngs)
        )
        if venues
        else _DEFAULT_BOUNDS
    )
    return VenueMapResponse(count=len(venues), bounds=bounds, venues=venues)
