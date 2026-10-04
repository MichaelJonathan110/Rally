"""Activity-type registry - now a SHIM over the sports catalog.

RALLY is sports-only, so the single source of truth for "what kind of activity
can I create" is :mod:`app.core.sports`. This module keeps the historical
``/activity-types`` wire shape but derives every row from the sports catalog,
so the endpoint, the seed script and the web app can never drift from the real
sports list.

The old generic registry (boardgame/kopdar/nobar/musik/seni/sketsa/camping...)
is kept under the ``LEGACY_*`` names purely so the demo seed script - which
still creates one demo row per legacy type - keeps importing cleanly. New code
must use the sports-derived symbols.
"""
from __future__ import annotations

from app.core.sports import SPORTS_PAYLOAD

#: Sports-derived activity types: (slug, label_id, label_en, category, title_template).
#: ``title_template`` always embeds the venue name via ``{v}``.
ACTIVITY_TYPES: list[tuple[str, str, str, str, str]] = [
    (
        str(row["slug"]),
        str(row["label_id"]),
        str(row["label_en"]),
        str(row["category"]),
        f"{row['label_id']} di {{v}}",
    )
    for row in SPORTS_PAYLOAD
]

#: Wire payload for ``GET /api/v1/activity-types`` (slug + labels + sport category).
ACTIVITY_TYPES_PAYLOAD: list[dict[str, str]] = [
    {"slug": slug, "label_id": label_id, "label_en": label_en, "category": category}
    for slug, label_id, label_en, category, _title in ACTIVITY_TYPES
]

#: slug -> {label_id, label_en, category, title}
ACTIVITY_TYPE_BY_SLUG: dict[str, dict[str, str]] = {
    slug: {
        "label_id": label_id,
        "label_en": label_en,
        "category": category,
        "title": title,
    }
    for slug, label_id, label_en, category, title in ACTIVITY_TYPES
}

#: Valid slugs (sports catalog slugs), used to validate incoming filters/creates.
ACTIVITY_TYPE_SLUGS: frozenset[str] = frozenset(ACTIVITY_TYPE_BY_SLUG)


# --------------------------------------------------------------------------
# Legacy generic registry - DEMO SEED ONLY. Not used by the API.
# --------------------------------------------------------------------------
LEGACY_ACTIVITY_TYPES: list[tuple[str, str, str, str, str]] = [
    # sports
    ("padel", "Padel", "Padel", "sports", "Main Padel di {v}"),
    ("badminton", "Badminton", "Badminton", "sports", "Sparring Badminton di {v}"),
    ("basket", "Basket", "Basketball", "sports", "Basket Bareng di {v}"),
    ("billiard", "Biliar", "Billiard", "sports", "Main Biliar di {v}"),
    ("futsal", "Futsal", "Futsal", "sports", "Futsal di {v}"),
    ("tenis", "Tenis", "Tennis", "sports", "Tenis di {v}"),
    ("renang", "Renang", "Swimming", "sports", "Renang di {v}"),
    # fitness
    ("lari", "Lari", "Running", "fitness", "Lari Pagi di {v}"),
    ("gym", "Gym", "Gym", "fitness", "Latihan Gym di {v}"),
    ("yoga", "Yoga", "Yoga", "fitness", "Kelas Yoga di {v}"),
    ("sepeda", "Sepeda", "Cycling", "fitness", "Gowes Santai di {v}"),
    # outdoor
    ("hiking", "Hiking", "Hiking", "outdoor", "Hiking di {v}"),
    ("gowes", "Gowes", "Cycling", "outdoor", "Gowes Bareng di {v}"),
    ("panjat", "Panjat Tebing", "Climbing", "outdoor", "Panjat Tebing di {v}"),
    ("camping", "Camping", "Camping", "outdoor", "Camping di {v}"),
    # games
    ("boardgame", "Board Game", "Board Game", "games", "Board Game Night di {v}"),
    ("esport", "E-Sport", "E-Sports", "games", "Turnamen E-Sport di {v}"),
    # social
    ("kopdar", "Kopdar", "Meetup", "social", "Kopdar di {v}"),
    ("nobar", "Nobar", "Watch Party", "social", "Nobar Bareng di {v}"),
    # creative
    ("musik", "Musik", "Music", "creative", "Jam Musik di {v}"),
    ("seni", "Seni", "Art", "creative", "Kelas Seni di {v}"),
    ("sketsa", "Sketsa", "Sketching", "creative", "Sketsa Bareng di {v}"),
]

LEGACY_ACTIVITY_TYPES_PAYLOAD: list[dict[str, str]] = [
    {"slug": slug, "label_id": label_id, "label_en": label_en, "category": category}
    for slug, label_id, label_en, category, _title in LEGACY_ACTIVITY_TYPES
]

LEGACY_ACTIVITY_TYPE_BY_SLUG: dict[str, dict[str, str]] = {
    slug: {
        "label_id": label_id,
        "label_en": label_en,
        "category": category,
        "title": title,
    }
    for slug, label_id, label_en, category, title in LEGACY_ACTIVITY_TYPES
}

LEGACY_ACTIVITY_TYPE_SLUGS: frozenset[str] = frozenset(LEGACY_ACTIVITY_TYPE_BY_SLUG)

__all__ = [
    "ACTIVITY_TYPES",
    "ACTIVITY_TYPES_PAYLOAD",
    "ACTIVITY_TYPE_BY_SLUG",
    "ACTIVITY_TYPE_SLUGS",
    "LEGACY_ACTIVITY_TYPES",
    "LEGACY_ACTIVITY_TYPES_PAYLOAD",
    "LEGACY_ACTIVITY_TYPE_BY_SLUG",
    "LEGACY_ACTIVITY_TYPE_SLUGS",
]
