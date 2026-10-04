"""User progress / streak computation (read-only).

Everything is derived from EXISTING tables - no new tables or columns. An
"active day" is any UTC calendar date on which the user did something real:
checked in, joined an activity, or hosted one.
"""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.activity import Activity, ActivityParticipant
from app.models.match import MatchParticipant
from app.models.social import CheckIn
from app.models.user import User
from app.schemas.discovery import (
    DayCount,
    StreakAchievement,
    UserProgress,
    WeeklyCount,
)

#: (code, name, description, icon, points, target, metric)
_ACHIEVEMENT_CATALOG: list[tuple[str, str, str, str, int, int, str]] = [
    (
        "first_activity", "Langkah Pertama", "Selesaikan kegiatan pertamamu",
        "activity", 10, 1, "activities_total",
    ),
    ("activity_5", "Rajin Gerak", "Ikut 5 kegiatan", "flame", 25, 5, "activities_total"),
    (
        "activity_25", "Atlet Sejati", "Ikut 25 kegiatan",
        "trophy", 100, 25, "activities_total",
    ),
    ("streak_3", "Api Menyala", "Streak 3 hari", "zap", 20, 3, "longest_streak"),
    ("streak_7", "Seminggu Penuh", "Streak 7 hari", "zap", 50, 7, "longest_streak"),
    ("streak_30", "Sebulan Konsisten", "Streak 30 hari", "crown", 200, 30, "longest_streak"),
    (
        "host_1", "Tuan Rumah", "Buat kegiatan pertamamu",
        "home", 30, 1, "activities_hosted",
    ),
    (
        "match_10", "Petarung", "Mainkan 10 pertandingan",
        "swords", 80, 10, "matches_played",
    ),
    (
        "explorer_3", "Penjelajah", "Coba 3 kategori olahraga",
        "compass", 40, 3, "distinct_categories",
    ),
]

_WEEKS = 8
_CALENDAR_DAYS = 90


def _utc_date(value: datetime | None) -> date | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.date()
    return value.astimezone(UTC).date()


class ProgressService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _active_dates(self, user_id: uuid.UUID) -> set[date]:
        dates: set[date] = set()

        for (ts,) in self.db.execute(
            select(CheckIn.checked_in_at).where(CheckIn.user_id == user_id)
        ).all():
            day = _utc_date(ts)
            if day is not None:
                dates.add(day)

        for (ts,) in self.db.execute(
            select(ActivityParticipant.joined_at).where(
                ActivityParticipant.user_id == user_id
            )
        ).all():
            day = _utc_date(ts)
            if day is not None:
                dates.add(day)

        for (ts,) in self.db.execute(
            select(Activity.created_at).where(Activity.host_id == user_id)
        ).all():
            day = _utc_date(ts)
            if day is not None:
                dates.add(day)

        return dates

    @staticmethod
    def _streaks(dates: set[date], today: date) -> tuple[int, int, date | None]:
        if not dates:
            return 0, 0, None
        ordered = sorted(dates)
        longest = 1
        run = 1
        for prev, cur in zip(ordered, ordered[1:], strict=False):
            if (cur - prev).days == 1:
                run += 1
            else:
                run = 1
            longest = max(longest, run)

        last = ordered[-1]
        yesterday = today - timedelta(days=1)
        anchor = today if today in dates else (yesterday if yesterday in dates else None)
        current = 0
        if anchor is not None:
            cursor = anchor
            while cursor in dates:
                current += 1
                cursor -= timedelta(days=1)
        return current, longest, last

    def compute(self, user_id: uuid.UUID) -> UserProgress:
        user = self.db.get(User, user_id)
        if user is None:
            raise NotFoundError("User not found")

        today = datetime.now(UTC).date()
        dates = self._active_dates(user_id)
        current_streak, longest_streak, last_active = self._streaks(dates, today)

        joined_ids = list(
            self.db.scalars(
                select(ActivityParticipant.activity_id).where(
                    ActivityParticipant.user_id == user_id
                )
            ).all()
        )
        activities_joined = len(set(joined_ids))
        activities_hosted = int(
            self.db.scalar(
                select(func.count()).select_from(Activity).where(Activity.host_id == user_id)
            )
            or 0
        )
        matches_played = int(
            self.db.scalar(
                select(func.count())
                .select_from(MatchParticipant)
                .where(MatchParticipant.user_id == user_id)
            )
            or 0
        )

        categories: set[str] = set()
        hosted_categories = self.db.scalars(
            select(Activity.category).where(Activity.host_id == user_id)
        ).all()
        categories.update(str(c) for c in hosted_categories if c is not None)
        if joined_ids:
            joined_categories = self.db.scalars(
                select(Activity.category).where(Activity.id.in_(joined_ids))
            ).all()
            categories.update(str(c) for c in joined_categories if c is not None)
        distinct_categories = len(categories)

        # Weekly buckets: last 8 ISO weeks (Monday start), including the current.
        this_monday = today - timedelta(days=today.weekday())
        weekly: list[WeeklyCount] = []
        for offset in range(_WEEKS - 1, -1, -1):
            week_start = this_monday - timedelta(weeks=offset)
            week_end = week_start + timedelta(days=7)
            count = sum(1 for d in dates if week_start <= d < week_end)
            weekly.append(WeeklyCount(week_start=week_start, count=count))

        window_start = today - timedelta(days=_CALENDAR_DAYS - 1)
        calendar = [
            DayCount(date=d, count=1)
            for d in sorted(dates)
            if window_start <= d <= today
        ]

        metrics = {
            "activities_total": activities_joined,
            "activities_hosted": activities_hosted,
            "matches_played": matches_played,
            "longest_streak": longest_streak,
            "distinct_categories": distinct_categories,
        }
        achievements = [
            StreakAchievement(
                code=code,
                name=name,
                description=description,
                icon=icon,
                points=points,
                target=target,
                progress=metrics.get(metric, 0),
                earned=metrics.get(metric, 0) >= target,
                earned_at=None,
            )
            for code, name, description, icon, points, target, metric in _ACHIEVEMENT_CATALOG
        ]

        return UserProgress(
            user_id=user_id,
            current_streak=current_streak,
            longest_streak=longest_streak,
            total_active_days=len(dates),
            last_active_date=last_active,
            activities_joined=activities_joined,
            activities_hosted=activities_hosted,
            matches_played=matches_played,
            distinct_categories=distinct_categories,
            weekly=weekly,
            calendar=calendar,
            achievements=achievements,
        )
