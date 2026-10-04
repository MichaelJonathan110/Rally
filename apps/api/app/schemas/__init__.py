"""Pydantic request/response schemas."""
from __future__ import annotations

from app.schemas.activity import (
    ActivityCategoryLinkCreate,
    ActivityCategoryLinkRead,
    ActivityCreate,
    ActivityParticipantRead,
    ActivityRead,
    ActivityUpdate,
    MyActivitiesRead,
    MyActivityGroups,
    MyActivityRead,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterResponse,
    TokenPair,
)
from app.schemas.booking import (
    BookingCreate,
    BookingRead,
    BookingUpdate,
    PaymentRead,
    PaymentSplitRead,
)
from app.schemas.club import ClubCreate, ClubMemberRead, ClubRead, ClubUpdate
from app.schemas.common import ORMModel, Page, Pagination
from app.schemas.user import (
    ProfileRead,
    UserBase,
    UserCreate,
    UserRead,
    UserSkillRead,
    UserUpdate,
)
from app.schemas.venue import (
    VenueAvailabilityRead,
    VenueAvailabilitySummary,
    VenueCourtCreate,
    VenueCourtRead,
    VenueCreate,
    VenueRead,
    VenueResourceRead,
    VenueUpdate,
)

__all__ = [
    "ORMModel",
    "Page",
    "Pagination",
    # user
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "ProfileRead",
    "UserSkillRead",
    # auth
    "LoginRequest",
    "LoginResponse",
    "RefreshRequest",
    "RegisterResponse",
    "TokenPair",
    # activity
    "ActivityCategoryLinkCreate",
    "ActivityCategoryLinkRead",
    "ActivityCreate",
    "ActivityUpdate",
    "ActivityRead",
    "ActivityParticipantRead",
    "MyActivityRead",
    "MyActivityGroups",
    "MyActivitiesRead",
    # venue
    "VenueCreate",
    "VenueUpdate",
    "VenueRead",
    "VenueCourtCreate",
    "VenueCourtRead",
    "VenueAvailabilityRead",
    "VenueAvailabilitySummary",
    "VenueResourceRead",
    # club
    "ClubCreate",
    "ClubUpdate",
    "ClubRead",
    "ClubMemberRead",
    # booking
    "BookingCreate",
    "BookingUpdate",
    "BookingRead",
    "PaymentRead",
    "PaymentSplitRead",
]
