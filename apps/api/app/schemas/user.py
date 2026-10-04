"""User-facing Pydantic schemas (request/response contracts)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.passwords import validate_password

from app.models.enums import SkillLevel, UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    """Public registration payload."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return validate_password(v)


class UserUpdate(BaseModel):
    """Self-service profile update; all fields optional."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    display_name: str | None = Field(default=None, max_length=80)
    bio: str | None = None
    avatar_url: str | None = Field(default=None, max_length=512)
    city: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=2)
    skill_level: SkillLevel | None = None


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    city: str | None = None
    country: str | None = None
    skill_level: SkillLevel
    reputation_score: int


class UserRead(BaseModel):
    """Public-safe user representation. Never includes hashed_password."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    email_verified: bool = False
    created_at: datetime
    profile: ProfileRead | None = None


class UserSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    level: SkillLevel
    years_experience: int


class UserSportRead(BaseModel):
    """A user's SPORT-SPECIFIC profile slice, read from real state.

    ``rating``/``ranked`` come from the existing ``MmrRating`` row for
    ``(user, sport)``. A user with a rating row but no verified matches is
    exposed as UNRANKED (``ranked=False``, ``rating=None``) - never a fake
    number.
    """

    sport_slug: str
    label: str
    skill_level: SkillLevel
    matches_played: int
    rating: float | None = None
    ranked: bool = False
