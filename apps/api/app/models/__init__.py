"""SQLAlchemy models. Importing this package registers every table on Base.metadata.

Alembic autogenerate relies on all models being imported here.
"""
from __future__ import annotations

from app.db.base import Base
from app.models.activity import Activity, ActivityCategoryLink, ActivityParticipant
from app.models.booking import Booking, Payment, PaymentSplit
from app.models.club import Club, ClubMember
from app.models.enums import (
    ActivityCategory,
    ActivityVisibility,
    BookingStatus,
    ParticipantStatus,
    PaymentStatus,
    SkillLevel,
    SplitStatus,
    UserRole,
)
from app.models.user import Profile, User
from app.models.venue import Venue, VenueCourt

__all__ = [
    "Base",
    # enums
    "UserRole",
    "ActivityCategory",
    "ActivityVisibility",
    "BookingStatus",
    "PaymentStatus",
    "ParticipantStatus",
    "SkillLevel",
    "SplitStatus",
    # user
    "User",
    "Profile",
    # activity
    "Activity",
    "ActivityCategoryLink",
    "ActivityParticipant",
    # venue
    "Venue",
    "VenueCourt",
    # club
    "Club",
    "ClubMember",
    # booking
    "Booking",
    "Payment",
    "PaymentSplit",
]
