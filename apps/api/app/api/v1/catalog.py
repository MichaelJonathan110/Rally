"""Catalog helpers: city list and activity-type registry.

These power the city-aware / type-aware discovery UI without touching the
existing activity or venue response shapes.

RALLY is sports-only: the activity-type registry is the SPORTS CATALOG itself
(:mod:`app.core.sports`). The historical ``/activity-types`` wire shape is kept,
but every row is a sport, tagged with its sport category (racket/team/combat/...).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.cities import CITIES, CITY_PROVINCE, PROVINCE_ORDER, PROVINCES
from app.core.sports import SPORTS_PAYLOAD
from app.models.activity import Activity
from app.models.venue import Venue

router = APIRouter(tags=["catalog"])

DbSession = Annotated[Session, Depends(get_db)]


class CityCount(BaseModel):
    """A city, its province and how many (live) activities it hosts."""

    city: str
    province: str | None = None
    count: int


class ProvinceRead(BaseModel):
    """A province and the autonomous cities it contains."""

    province: str
    cities: list[str]


class ActivityTypeRead(BaseModel):
    """A sport from the sports catalog, exposed as an activity type.

    ``category`` is the SPORT category (racket/team/combat/...), so the
    discovery UI groups activities by real sport type.
    """

    slug: str
    label_id: str
    label_en: str
    category: str


@router.get("/cities", response_model=list[CityCount])
def list_cities(db: DbSession) -> list[CityCount]:
    """ALL Indonesian autonomous cities, each with its live activity count.

    The list is the master reference dataset (every kota otonom), so the city
    picker always shows the whole country - cities without any seeded content
    come back with ``count == 0``. Sorted by activity count (busiest first),
    then alphabetically.
    """
    rows = db.execute(
        select(Venue.city, func.count(Activity.id))
        .join(Activity, Activity.venue_id == Venue.id)
        .where(Activity.is_cancelled.is_(False))
        .group_by(Venue.city)
    ).all()
    counts = {city: int(count) for city, count in rows}
    payload = [
        CityCount(city=city, province=province, count=counts.get(city, 0))
        for city, province in CITIES
    ]
    # Also surface any city present in the DB but missing from the reference
    # list, so data never silently disappears from the picker.
    known = {city for city, _ in CITIES}
    for city, count in counts.items():
        if city not in known:
            payload.append(
                CityCount(city=city, province=CITY_PROVINCE.get(city), count=count)
            )
    payload.sort(key=lambda c: (-c.count, c.city))
    return payload


@router.get("/provinces", response_model=list[ProvinceRead])
def list_provinces() -> list[ProvinceRead]:
    """Provinces (geographic order) with the autonomous cities they contain."""
    ordered = [p for p in PROVINCE_ORDER if p in PROVINCES]
    ordered += [p for p in PROVINCES if p not in ordered]
    return [
        ProvinceRead(province=p, cities=sorted(PROVINCES[p])) for p in ordered
    ]


@router.get("/activity-types", response_model=list[ActivityTypeRead])
def list_activity_types() -> list[ActivityTypeRead]:
    """The activity-type registry - sourced from the SPORTS CATALOG.

    Every row is a sport (slug/labels + sport category), so the create UI can
    only ever offer real sports.
    """
    return [
        ActivityTypeRead(
            slug=str(row["slug"]),
            label_id=str(row["label_id"]),
            label_en=str(row["label_en"]),
            category=str(row["category"]),
        )
        for row in SPORTS_PAYLOAD
    ]
