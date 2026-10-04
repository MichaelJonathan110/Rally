"""Matchmaking recommendations (read-only).

Scores future activities and peer players for a user purely from EXISTING
tables. Nothing is persisted and no table/column is created.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.activity import Activity, ActivityParticipant
from app.models.enums import ActivityVisibility, ParticipantStatus
from app.models.rating import MmrRating
from app.models.user import Profile, User
from app.schemas.discovery import (
    MatchmakingActivity,
    MatchmakingPartner,
    MatchmakingResponse,
)

_DEFAULT_INTERESTS = ["racket", "team", "combat"]
_ACTIVE_STATUSES = (
    ParticipantStatus.CONFIRMED,
    ParticipantStatus.ATTENDED,
    ParticipantStatus.REQUESTED,
    ParticipantStatus.WAITLISTED,
)


class MatchmakingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _interests(self, user_id: uuid.UUID) -> list[str]:
        joined_ids = list(
            self.db.scalars(
                select(ActivityParticipant.activity_id).where(
                    ActivityParticipant.user_id == user_id
                )
            ).all()
        )
        found: set[str] = set()
        hosted = self.db.scalars(
            select(Activity.category).where(Activity.host_id == user_id)
        ).all()
        found.update(str(c) for c in hosted if c is not None)
        if joined_ids:
            joined = self.db.scalars(
                select(Activity.category).where(Activity.id.in_(joined_ids))
            ).all()
            found.update(str(c) for c in joined if c is not None)
        mmr_cats = self.db.scalars(
            select(MmrRating.category).where(MmrRating.user_id == user_id)
        ).all()
        found.update(str(c) for c in mmr_cats if c is not None)
        return sorted(found) if found else list(_DEFAULT_INTERESTS)

    def _user_city(self, user_id: uuid.UUID) -> str | None:
        profile = self.db.scalar(select(Profile).where(Profile.user_id == user_id))
        return profile.city if profile is not None else None

    def recommend(self, user_id: uuid.UUID, limit: int = 8) -> MatchmakingResponse:
        user = self.db.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")

        interests = self._interests(user_id)
        interest_set = set(interests)
        city = self._user_city(user_id)
        now = datetime.now(UTC)

        joined_ids = set(
            self.db.scalars(
                select(ActivityParticipant.activity_id).where(
                    ActivityParticipant.user_id == user_id
                )
            ).all()
        )

        candidates = self.db.scalars(
            select(Activity)
            .where(
                Activity.starts_at >= now,
                Activity.is_cancelled.is_(False),
                Activity.host_id != user_id,
                Activity.visibility != ActivityVisibility.PRIVATE,
            )
            .order_by(Activity.starts_at.asc())
            .limit(200)
        ).all()

        activities: list[MatchmakingActivity] = []
        for activity in candidates:
            if activity.id in joined_ids:
                continue
            category = str(activity.category)
            pcount = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(ActivityParticipant)
                    .where(
                        ActivityParticipant.activity_id == activity.id,
                        ActivityParticipant.status.in_(
                            [str(s) for s in _ACTIVE_STATUSES]
                        ),
                    )
                )
                or 0
            )
            score = 60
            reasons: list[tuple[int, str]] = []
            sport_category = (
                str(activity.sport_category) if activity.sport_category else None
            )
            matched = category if category in interest_set else None
            if matched is None and sport_category in interest_set:
                matched = sport_category
            if matched is not None:
                score += 25
                reasons.append((25, "sesuai minat " + matched))
            venue = activity.venue
            venue_city = venue.city if venue is not None else None
            if city is not None and venue_city == city:
                score += 10
                reasons.append((10, "dekat di " + city))
            if activity.max_participants > 0 and pcount < activity.max_participants * 0.5:
                score += 5
                reasons.append((5, "masih banyak slot"))
            reasons.sort(key=lambda r: r[0], reverse=True)
            reason = reasons[0][1] if reasons else "kegiatan rekomendasi"

            activities.append(
                MatchmakingActivity(
                    id=activity.id,
                    title=activity.title,
                    category=category,
                    sport_slug=activity.sport_slug,
                    sport_category=sport_category,
                    city=venue_city,
                    venue_name=venue.name if venue is not None else None,
                    starts_at=activity.starts_at,
                    cost_per_person_cents=activity.cost_per_person_cents,
                    currency=activity.currency,
                    participant_count=pcount,
                    max_participants=activity.max_participants,
                    skill_level=str(activity.skill_level),
                    match_score=score,
                    reason=reason,
                )
            )

        activities.sort(key=lambda a: a.match_score, reverse=True)

        partners = self._partners(user_id, interest_set, city)
        return MatchmakingResponse(
            city=city,
            interests=interests,
            activities=activities[:limit],
            partners=partners[:limit],
        )

    def _partners(
        self, user_id: uuid.UUID, interests: set[str], city: str | None
    ) -> list[MatchmakingPartner]:
        rating_rows = self.db.execute(
            select(MmrRating.user_id, MmrRating.category).where(
                MmrRating.user_id != user_id,
                MmrRating.category.in_(list(interests)),
            )
        ).all()
        shared: dict[uuid.UUID, set[str]] = {}
        for uid, category in rating_rows:
            shared.setdefault(uid, set()).add(str(category))

        hosted_rows = self.db.execute(
            select(Activity.host_id, Activity.category, Activity.sport_category).where(
                Activity.host_id != user_id,
            )
        ).all()
        for uid, category, sport_category in hosted_rows:
            cat = str(category) if category is not None else None
            scat = str(sport_category) if sport_category is not None else None
            if cat in interests:
                shared.setdefault(uid, set()).add(cat)
            if scat in interests:
                shared.setdefault(uid, set()).add(scat)

        if not shared:
            return []

        profiles = {
            p.user_id: p
            for p in self.db.scalars(
                select(Profile).where(Profile.user_id.in_(list(shared.keys())))
            ).all()
        }

        partners: list[MatchmakingPartner] = []
        for uid, cats in shared.items():
            profile = profiles.get(uid)
            display_name = (
                profile.display_name if profile is not None else "Pengguna RALLY"
            )
            p_city = profile.city if profile is not None else None
            category = sorted(cats)[0] if cats else None
            rating_row = None
            if category is not None:
                rating_row = self.db.scalar(
                    select(MmrRating).where(
                        MmrRating.user_id == uid, MmrRating.category == category
                    )
                )
            games_played = int(rating_row.games_played) if rating_row is not None else 0
            rating = (
                float(rating_row.rating)
                if rating_row is not None and games_played > 0
                else None
            )

            score = 60 + 25 * len(cats)
            if city is not None and p_city == city:
                score += 10

            partners.append(
                MatchmakingPartner(
                    user_id=uid,
                    display_name=display_name,
                    city=p_city,
                    shared_categories=sorted(cats),
                    category=category,
                    rating=rating,
                    games_played=games_played,
                    match_score=score,
                )
            )

        partners.sort(key=lambda p: p.match_score, reverse=True)
        return partners
