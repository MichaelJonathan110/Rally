"""Match, result-verification, leaderboard and rating schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import MatchResultStatus, MatchStatus
from app.schemas.common import ORMModel


class MatchParticipantCreate(BaseModel):
    """One participant on a team (team 0 = A, team 1 = B)."""

    user_id: uuid.UUID
    team: int = Field(default=0, ge=0, le=1)
    score: int = Field(default=0, ge=0, le=1000)


class MatchCreate(BaseModel):
    """Host records a match with its participants."""

    participants: list[MatchParticipantCreate] = Field(min_length=2)
    scheduled_at: datetime | None = None


class MatchParticipantRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    team: int
    is_winner: bool | None = None
    score: int


class ResultSubmit(BaseModel):
    """Submit the final score for a match."""

    team_a_score: int = Field(ge=0, le=1000)
    team_b_score: int = Field(ge=0, le=1000)
    notes: str | None = Field(default=None, max_length=2000)


class MatchResultRead(ORMModel):
    id: uuid.UUID
    match_id: uuid.UUID
    submitted_by_id: uuid.UUID
    status: MatchResultStatus
    team_a_score: int
    team_b_score: int
    winner_team: int | None = None
    notes: str | None = None
    mmr_applied: bool
    verified_at: datetime | None = None


class MatchRead(ORMModel):
    id: uuid.UUID
    activity_id: uuid.UUID | None = None
    tournament_id: uuid.UUID | None = None
    status: MatchStatus
    scheduled_at: datetime | None = None
    played_at: datetime | None = None
    participants: list[MatchParticipantRead] = Field(default_factory=list)
    results: list[MatchResultRead] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    """A participant confirms or disputes a submitted result."""

    result_id: uuid.UUID
    confirmed: bool = True
    comment: str | None = Field(default=None, max_length=500)


class LeaderboardEntryRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    #: Sport scope key (sport slug, or ``category:<cat>`` for legacy rows).
    sport_slug: str
    period: str
    rank: int
    rating: float
    games_played: int
    computed_at: datetime | None = None


class StandingRead(BaseModel):
    """A user's standing in a single sport leaderboard.

    ``ranked`` is ``False`` and ``rank`` is ``None`` for players with no verified
    matches in the sport (the **UNRANKED** state).
    """

    user_id: uuid.UUID
    sport_slug: str
    ranked: bool
    rank: int | None = None
    rating: float | None = None
    games_played: int = 0


class SportLeaderboardRead(BaseModel):
    """A per-sport leaderboard plus the caller's own standing in it."""

    sport_slug: str
    period: str
    entries: list[LeaderboardEntryRead]
    me: StandingRead


class MmrRatingRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    category: str
    #: Sport scope key (sport slug, or ``category:<cat>`` for legacy rows).
    sport_slug: str
    rating: float
    games_played: int
    wins: int
    losses: int
    draws: int


class MmrHistoryRead(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_result_id: uuid.UUID | None = None
    rating_before: float
    rating_after: float
    delta: float
    reason: str
    created_at: datetime


class UserRatingsRead(ORMModel):
    """A user's ratings plus recent history."""

    user_id: uuid.UUID
    ratings: list[MmrRatingRead]
    history: list[MmrHistoryRead]
