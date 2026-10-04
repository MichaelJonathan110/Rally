"""Sports catalog endpoints - the extensible sports registry."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.sports import CATEGORY_SPORTS, SPORT_BY_SLUG, SPORT_CATEGORIES, SPORTS_PAYLOAD

router = APIRouter(tags=["sports"])


class SportCategoryRead(BaseModel):
    slug: str
    label_id: str
    label_en: str
    blurb: str
    sport_count: int


class SportRead(BaseModel):
    slug: str
    label_id: str
    label_en: str
    category: str
    venue_kind: str
    resource_label: str
    competitive: bool
    variants: list[str]
    formats: list[str]
    metrics: list[str]


@router.get("/sport-categories", response_model=list[SportCategoryRead])
def list_sport_categories() -> list[SportCategoryRead]:
    """All top-level sport categories, each with its sport count."""
    return [
        SportCategoryRead(
            slug=slug,
            label_id=label_id,
            label_en=label_en,
            blurb=blurb,
            sport_count=len(CATEGORY_SPORTS.get(slug, [])),
        )
        for slug, label_id, label_en, blurb in SPORT_CATEGORIES
    ]


@router.get("/sports", response_model=list[SportRead])
def list_sports(category: str | None = None, q: str | None = None) -> list[SportRead]:
    """The full sports catalog, optionally filtered by category or search term."""
    rows = SPORTS_PAYLOAD
    if category:
        rows = [r for r in rows if r["category"] == category]
    if q:
        needle = q.strip().lower()
        rows = [
            r
            for r in rows
            if needle in str(r["label_id"]).lower()
            or needle in str(r["label_en"]).lower()
            or needle in str(r["slug"])
        ]
    return [SportRead(**r) for r in rows]


@router.get("/sports/{slug}", response_model=SportRead)
def get_sport(slug: str) -> SportRead:
    row = SPORT_BY_SLUG.get(slug)
    if row is None:
        raise HTTPException(status_code=404, detail="Sport not found")
    return SportRead(**row)
