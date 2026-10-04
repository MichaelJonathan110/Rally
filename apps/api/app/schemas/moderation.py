"""Schemas for reports, reviews, achievements and admin/moderation actions."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.sanitize import clean_text
from app.models.enums import (
    ModerationActionType,
    ReportStatus,
    ReportTargetType,
    ReviewTargetType,
    UserRole,
)


# --- Reports ---------------------------------------------------------------
class ReportCreate(BaseModel):
    """Any authenticated user may file a report."""

    target_type: ReportTargetType
    target_id: uuid.UUID
    reason: str = Field(min_length=3, max_length=255)
    details: str | None = Field(default=None, max_length=4000)

    @field_validator("reason")
    @classmethod
    def _clean_reason(cls, v: str) -> str:
        return clean_text(v, max_length=255)

    @field_validator("details")
    @classmethod
    def _clean_details(cls, v: str | None) -> str | None:
        return clean_text(v, max_length=4000) if v is not None else None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reporter_id: uuid.UUID
    target_type: ReportTargetType
    target_id: uuid.UUID
    reason: str
    details: str | None = None
    status: ReportStatus
    resolved_by_id: uuid.UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class ReportResolveRequest(BaseModel):
    status: ReportStatus = ReportStatus.RESOLVED
    note: str | None = Field(default=None, max_length=1000)
    action: ModerationActionType | None = None


# --- Moderation log --------------------------------------------------------
class ModerationActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID | None = None
    moderator_id: uuid.UUID
    target_user_id: uuid.UUID | None = None
    action: ModerationActionType
    reason: str | None = None
    expires_at: datetime | None = None
    created_at: datetime


# --- Admin: role + ban -----------------------------------------------------
class RoleChangeRequest(BaseModel):
    role: UserRole


class BanRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)
    # Optional ban duration; None = permanent.
    duration_hours: int | None = Field(default=None, ge=1, le=24 * 365)


# --- Reviews ---------------------------------------------------------------
class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str | None = Field(default=None, max_length=4000)

    @field_validator("body")
    @classmethod
    def _clean_body(cls, v: str | None) -> str | None:
        return clean_text(v, max_length=4000) if v is not None else None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author_id: uuid.UUID
    target_type: ReviewTargetType
    target_id: uuid.UUID
    rating: int
    body: str | None = None
    created_at: datetime


class VenueRatingSummary(BaseModel):
    venue_id: uuid.UUID
    average_rating: float
    review_count: int
    reviews: list[ReviewRead]


# --- Achievements ----------------------------------------------------------
class AchievementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    points: int


class UserAchievementRead(BaseModel):
    achievement: AchievementRead
    earned_at: datetime | None = None
