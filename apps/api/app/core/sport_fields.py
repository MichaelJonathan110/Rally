"""Sport-specific activity fields, resolved against the sports catalog.

RALLY is sports-only: an activity names the sport it is for (a slug from
:mod:`app.core.sports`) and that sport's catalog row drives the allowed
variants/formats and the default tracked metrics. This module is the single
place that resolves and validates those fields - both the API schemas and the
service layer use it, so there is exactly one source of truth.
"""
from __future__ import annotations

from typing import Any

from app.core.sports import SPORT_BY_SLUG, SPORT_SLUGS
from app.models.enums import ActivityCategory


class SportFieldError(ValueError):
    """A sport-specific field is invalid (unknown sport, bad variant/format)."""


def is_known_sport(sport_slug: str) -> bool:
    """True when ``sport_slug`` exists in the sports catalog."""
    return sport_slug in SPORT_SLUGS


def sport_catalog_row(sport_slug: str) -> dict[str, Any]:
    """The catalog row for ``sport_slug`` or raise :class:`SportFieldError`."""
    row = SPORT_BY_SLUG.get(sport_slug)
    if row is None:
        raise SportFieldError(f"Unknown sport slug {sport_slug!r}")
    return row


def resolve_sport_fields(
    *,
    sport_slug: str | None,
    variant: str | None = None,
    format: str | None = None,
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    """Validate sport-specific fields and return DB-ready values.

    Returns ``{}`` for a legacy activity (no ``sport_slug``); otherwise a dict
    with ``sport_slug``/``sport_category``/``variant``/``format``/``metrics``.

    Raises :class:`SportFieldError` when the slug is unknown, or when a chosen
    variant/format/metric is not allowed by the chosen sport's catalog row.
    """
    if sport_slug is None:
        if variant is not None or format is not None or metrics is not None:
            raise SportFieldError("variant/format/metrics require a sport_slug")
        return {}

    row = sport_catalog_row(sport_slug)
    variants = [str(v) for v in row["variants"]]  # type: ignore[union-attr]
    formats = [str(f) for f in row["formats"]]  # type: ignore[union-attr]
    catalog_metrics = [str(m) for m in row["metrics"]]  # type: ignore[union-attr]

    if variant is not None and variant not in variants:
        raise SportFieldError(
            f"variant {variant!r} is not allowed for {sport_slug!r}; "
            f"choose one of {variants or ['(none)']}"
        )
    if format is not None and format not in formats:
        raise SportFieldError(
            f"format {format!r} is not allowed for {sport_slug!r}; "
            f"choose one of {formats or ['(none)']}"
        )
    if metrics is None:
        chosen_metrics = catalog_metrics
    else:
        unknown = [m for m in metrics if m not in catalog_metrics]
        if unknown:
            raise SportFieldError(
                f"metrics {unknown} are not tracked for {sport_slug!r}; "
                f"allowed: {catalog_metrics}"
            )
        chosen_metrics = list(metrics)

    return {
        "sport_slug": sport_slug,
        "sport_category": row["category"],
        "variant": variant,
        "format": format,
        "metrics": chosen_metrics,
    }


#: Map a sports-catalog category to the legacy high-level ActivityCategory.
_SPORT_CATEGORY_TO_ACTIVITY_CATEGORY: dict[str, ActivityCategory] = {
    "outdoor": ActivityCategory.OUTDOOR,
}


def activity_category_for_sport(sport_category: str) -> ActivityCategory:
    """Legacy high-level ``ActivityCategory`` for a sports-catalog category.

    Sports map to ``SPORTS``; outdoor sports to ``OUTDOOR``. Kept so the legacy
    ``category`` columns stay populated for backward compatibility.
    """
    return _SPORT_CATEGORY_TO_ACTIVITY_CATEGORY.get(sport_category, ActivityCategory.SPORTS)


def resolve_club_sport(sport_slug: str) -> dict[str, str]:
    """Validate a club's sport and derive its category fields.

    Returns DB-ready ``sport_slug``/``sport_category``/``category`` values.
    Raises :class:`SportFieldError` when the slug is not in the sports catalog.
    """
    row = sport_catalog_row(sport_slug)
    sport_category = str(row["category"])
    return {
        "sport_slug": sport_slug,
        "sport_category": sport_category,
        "category": str(activity_category_for_sport(sport_category)),
    }


def sport_category_slug(sport_slug: str | None) -> str:
    """The catalog category slug for a sport (``racket``/``team``/...).

    Returns ``"other"`` for an unknown or missing sport so callers always have a
    concrete, back-compat grouping value to store.
    """
    if sport_slug:
        row = SPORT_BY_SLUG.get(sport_slug)
        if row is not None:
            return str(row["category"])
    return "other"


def is_competitive_sport(sport_slug: str | None) -> bool:
    """True only for catalog sports flagged ``competitive=True`` (MMR-bearing).

    Unknown or missing sports are **not** competitive - MMR must never change
    for them.
    """
    if not sport_slug:
        return False
    row = SPORT_BY_SLUG.get(sport_slug)
    return bool(row is not None and row["competitive"])
