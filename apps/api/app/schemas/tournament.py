"""Tournament request/response schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.sanitize import clean_text
from app.models.enums import ActivityCategory, TournamentFormat, TournamentStatus


class TournamentBase(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    category: ActivityCategory = ActivityCategory.SPORTS
    format: TournamentFormat = TournamentFormat.SINGLE_ELIMINATION
    max_entries: int = Field(default=16, ge=2, le=256)
    entry_fee_cents: int = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    venue_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        return clean_text(v, max_length=160)

    @field_validator("description")
    @classmethod
    def _clean_description(cls, v: str | None) -> str | None:
        return clean_text(v, max_length=4000) if v is not None else None


class TournamentCreate(TournamentBase):
    """Payload for creating a tournament. The caller becomes the organizer."""

    slug: str | None = Field(default=None, max_length=80)


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: TournamentStatus | None = None
    max_entries: int | None = Field(default=None, ge=2, le=256)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class TournamentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organizer_id: uuid.UUID
    venue_id: uuid.UUID | None = None
    slug: str
    name: str
    description: str | None = None
    category: ActivityCategory
    format: TournamentFormat
    status: TournamentStatus
    max_entries: int
    entry_fee_cents: int
    currency: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime


class TournamentEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tournament_id: uuid.UUID
    user_id: uuid.UUID
    seed: int | None = None
    eliminated: bool
    final_placement: int | None = None


class BracketMatchRead(BaseModel):
    """One bracket fixture, with resolved competitor ids for convenience."""

    id: uuid.UUID
    round_number: int
    slot: int
    home_entry_id: uuid.UUID | None = None
    away_entry_id: uuid.UUID | None = None
    home_user_id: uuid.UUID | None = None
    away_user_id: uuid.UUID | None = None
    winner_entry_id: uuid.UUID | None = None
    match_id: uuid.UUID | None = None
    status: str


class BracketRead(BaseModel):
    tournament_id: uuid.UUID
    format: TournamentFormat
    rounds: int
    matches: list[BracketMatchRead]


class RecordResultRequest(BaseModel):
    """Record the winner of a bracket fixture (organizer/admin only)."""

    bracket_match_id: uuid.UUID
    winner_entry_id: uuid.UUID
    home_score: int = Field(default=0, ge=0)
    away_score: int = Field(default=0, ge=0)


class StandingRow(BaseModel):
    rank: int
    entry_id: uuid.UUID
    user_id: uuid.UUID
    seed: int | None = None
    eliminated: bool
    final_placement: int | None = None


class StandingsRead(BaseModel):
    tournament_id: uuid.UUID
    status: TournamentStatus
    standings: list[StandingRow]
