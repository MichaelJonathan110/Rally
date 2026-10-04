"""SQLAlchemy models. Importing this package registers every table on Base.metadata.

Alembic autogenerate relies on all models being imported here.
"""
from __future__ import annotations

from app.db.base import Base
from app.models.activity import (
    Activity,
    ActivityCategoryLink,
    ActivityParticipant,
    ActivityRecurrence,
)
from app.models.booking import Booking, Payment, PaymentSplit, Refund
from app.models.club import Club, ClubJoinRequest, ClubMember
from app.models.enums import (
    ActivityCategory,
    ActivityVisibility,
    AuditAction,
    BookingStatus,
    ChatRoomType,
    ClubJoinRequestStatus,
    MatchResultStatus,
    MatchStatus,
    MessageType,
    ModerationActionType,
    NotificationType,
    ParticipantStatus,
    PaymentStatus,
    RecurrenceFrequency,
    RefundStatus,
    ReportStatus,
    ReportTargetType,
    ReviewTargetType,
    SkillLevel,
    SplitStatus,
    TournamentFormat,
    TournamentStatus,
    UserRole,
)
from app.models.follow import Follow
from app.models.match import (
    Match,
    MatchParticipant,
    MatchResult,
    ResultVerification,
)
from app.models.rating import LeaderboardEntry, MmrHistory, MmrRating
from app.models.social import (
    Achievement,
    ChatMessage,
    ChatRoom,
    CheckIn,
    ModerationAction,
    Notification,
    Report,
    Review,
    UserAchievement,
)
from app.models.token import OneTimeToken
from app.models.tournament import Tournament, TournamentEntry, TournamentMatch
from app.models.user import Profile, User, UserSkill
from app.models.venue import Venue, VenueAvailability, VenueCourt

__all__ = [
    "Base",
    # enums
    "UserRole",
    "ActivityCategory",
    "ActivityVisibility",
    "ParticipantStatus",
    "SkillLevel",
    "RecurrenceFrequency",
    "BookingStatus",
    "PaymentStatus",
    "SplitStatus",
    "RefundStatus",
    "ClubJoinRequestStatus",
    "MatchStatus",
    "MatchResultStatus",
    "TournamentFormat",
    "TournamentStatus",
    "ChatRoomType",
    "MessageType",
    "NotificationType",
    "ReviewTargetType",
    "ReportTargetType",
    "ReportStatus",
    "ModerationActionType",
    "AuditAction",
    # token
    "OneTimeToken",
    # user
    "User",
    "Profile",
    "UserSkill",
    # follow
    "Follow",
    # activity
    "Activity",
    "ActivityCategoryLink",
    "ActivityParticipant",
    "ActivityRecurrence",
    # venue
    "Venue",
    "VenueCourt",
    "VenueAvailability",
    # club
    "Club",
    "ClubMember",
    "ClubJoinRequest",
    # booking
    "Booking",
    "Payment",
    "PaymentSplit",
    "Refund",
    # match
    "Match",
    "MatchParticipant",
    "MatchResult",
    "ResultVerification",
    # rating
    "MmrRating",
    "MmrHistory",
    "LeaderboardEntry",
    # tournament
    "Tournament",
    "TournamentEntry",
    "TournamentMatch",
    # social
    "ChatRoom",
    "ChatMessage",
    "CheckIn",
    "Notification",
    "Review",
    "Achievement",
    "UserAchievement",
    "Report",
    "ModerationAction",
]
