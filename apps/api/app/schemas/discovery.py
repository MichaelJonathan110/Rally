"""Discovery, progress and venue-map read schemas (Pydantic v2).

Pure read models computed from existing tables - no persistence, no new columns.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class MatchmakingActivity(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    sport_slug: str | None = None
    sport_category: str | None = None
    city: str | None = None
    venue_name: str | None = None
    starts_at: datetime
    cost_per_person_cents: int
    currency: str
    participant_count: int
    max_participants: int
    skill_level: str
    match_score: int
    reason: str


class MatchmakingPartner(BaseModel):
    user_id: uuid.UUID
    display_name: str
    city: str | None = None
    shared_categories: list[str]
    category: str | None = None
    rating: float | None = None
    games_played: int
    match_score: int


class MatchmakingResponse(BaseModel):
    city: str | None = None
    interests: list[str]
    activities: list[MatchmakingActivity]
    partners: list[MatchmakingPartner]


class StreakAchievement(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    points: int
    target: int
    progress: int
    earned: bool
    earned_at: datetime | None = None


class WeeklyCount(BaseModel):
    week_start: date
    count: int


class DayCount(BaseModel):
    date: date
    count: int


class UserProgress(BaseModel):
    user_id: uuid.UUID
    current_streak: int
    longest_streak: int
    total_active_days: int
    last_active_date: date | None = None
    activities_joined: int
    activities_hosted: int
    matches_played: int
    distinct_categories: int
    weekly: list[WeeklyCount]
    calendar: list[DayCount]
    achievements: list[StreakAchievement]


class MapVenue(BaseModel):
    id: uuid.UUID
    name: str
    city: str
    province: str | None = None
    area: str | None = None
    category: str | None = None
    venue_kind: str | None = None
    latitude: float
    longitude: float
    court_count: int
    sport_slugs: list[str]


class VenueMapBounds(BaseModel):
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


class VenueMapResponse(BaseModel):
    count: int
    bounds: VenueMapBounds
    venues: list[MapVenue]
