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


class SportCategory(StrEnum):
    """Top-level sports grouping (config-driven sports catalog)."""

    RACKET = "racket"
    TEAM = "team"
    COMBAT = "combat"
    STRENGTH = "strength"
    RUNNING = "running"
    CYCLING = "cycling"
    WATER = "water"
    WINTER = "winter"
    PRECISION = "precision"
    GYMNASTICS = "gymnastics"
    OUTDOOR = "outdoor"
    OTHER = "other"


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


class RecurrenceFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


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


class RefundStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"
    FAILED = "failed"


class ClubJoinRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class MatchStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class MatchResultStatus(StrEnum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class TournamentFormat(StrEnum):
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"


class TournamentStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChatRoomType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"
    ACTIVITY = "activity"
    CLUB = "club"
    TOURNAMENT = "tournament"


class MessageType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


class NotificationType(StrEnum):
    ACTIVITY_INVITE = "activity_invite"
    JOIN_REQUEST = "join_request"
    BOOKING = "booking"
    PAYMENT = "payment"
    MATCH_RESULT = "match_result"
    MMR_UPDATE = "mmr_update"
    ACHIEVEMENT = "achievement"
    MODERATION = "moderation"
    SYSTEM = "system"


class ReviewTargetType(StrEnum):
    USER = "user"
    VENUE = "venue"
    ACTIVITY = "activity"
    CLUB = "club"


class ReportTargetType(StrEnum):
    USER = "user"
    ACTIVITY = "activity"
    MESSAGE = "message"
    REVIEW = "review"
    CLUB = "club"
    VENUE = "venue"


class ReportStatus(StrEnum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationActionType(StrEnum):
    WARN = "warn"
    MUTE = "mute"
    SUSPEND = "suspend"
    BAN = "ban"
    REMOVE_CONTENT = "remove_content"
    RESTORE_CONTENT = "restore_content"
    DISMISS_REPORT = "dismiss_report"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    MMR_UPDATE = "mmr_update"
    BOOKING = "booking"
    PAYMENT = "payment"
    MODERATION = "moderation"


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
