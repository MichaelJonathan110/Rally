"""Domain enumerations shared across models, schemas and services.

Stored as native PostgreSQL enums (SQLAlchemy ``Enum``). ``StrEnum`` keeps the
members JSON/string-friendly while remaining real enums.
"""
from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Enum


class UserRole(StrEnum):
    """RBAC roles. Server-enforced; the frontend is never the boundary."""

    USER = "user"
    HOST = "host"
    CLUB_ORGANIZER = "club_organizer"
    VENUE_MANAGER = "venue_manager"
    TOURNAMENT_ORGANIZER = "tournament_organizer"
    MODERATOR = "moderator"
    ADMIN = "admin"


class ActivityCategory(StrEnum):
    """High-level grouping for activity types (config-driven engine)."""

    SPORTS = "sports"
    GAMES = "games"
    OUTDOOR = "outdoor"
    SOCIAL = "social"
    CREATIVE = "creative"
    FITNESS = "fitness"
    OTHER = "other"


class ActivityVisibility(StrEnum):
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class ParticipantStatus(StrEnum):
    INVITED = "invited"
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    ANY = "any"


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    REFUNDED = "refunded"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class SplitStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    WAIVED = "waived"
    REFUNDED = "refunded"


def pg_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """Return a native PostgreSQL ENUM type that stores member *values*.

    SQLAlchemy's ``Enum`` stores member *names* by default; ``values_callable``
    forces it to persist the lowercase ``value`` of each ``StrEnum`` member so
    database rows match the JSON/API representation exactly.
    """
    return Enum(
        enum_cls,
        name=name,
        values_callable=lambda cls: [m.value for m in cls],
        native_enum=True,
        validate_strings=True,
    )
