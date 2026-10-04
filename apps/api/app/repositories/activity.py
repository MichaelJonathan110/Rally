"""Activity data access."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Select, case, func, or_, select

from app.models.activity import Activity, ActivityParticipant
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    model = Activity

    def get(self, entity_id: uuid.UUID) -> Activity | None:
        return self.db.get(Activity, entity_id)

    def _filtered(
        self,
        *,
        category: str | None = None,
        sport_slug: str | None = None,
        sport_category: str | None = None,
        activity_type: str | None = None,
        skill_level: str | None = None,
        city: str | None = None,
        venue_id: uuid.UUID | None = None,
        host_id: uuid.UUID | None = None,
        starts_after: object | None = None,
        starts_before: object | None = None,
        search: str | None = None,
        include_cancelled: bool = False,
    ) -> Select[tuple[Activity]]:
        stmt = select(Activity)
        if not include_cancelled:
            stmt = stmt.where(Activity.is_cancelled.is_(False))
        if category is not None:
            stmt = stmt.where(Activity.category == category)
        if sport_slug is not None:
            stmt = stmt.where(Activity.sport_slug == sport_slug)
        if sport_category is not None:
            stmt = stmt.where(Activity.sport_category == sport_category)
        if activity_type is not None:
            stmt = stmt.where(Activity.activity_type == activity_type)
        if skill_level is not None:
            stmt = stmt.where(Activity.skill_level == skill_level)
        if venue_id is not None:
            stmt = stmt.where(Activity.venue_id == venue_id)
        if host_id is not None:
            stmt = stmt.where(Activity.host_id == host_id)
        if starts_after is not None:
            stmt = stmt.where(Activity.starts_at >= starts_after)
        if starts_before is not None:
            stmt = stmt.where(Activity.starts_at <= starts_before)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Activity.title.ilike(like), Activity.description.ilike(like)))
        if city is not None:
            # Join the venue to filter by location without denormalising city.
            # Alias legacy spellings (Solo -> Surakarta, Jogja -> Yogyakarta...).
            from app.core.cities import canonical_city
            from app.models.venue import Venue

            stmt = stmt.join(Venue, Activity.venue_id == Venue.id).where(
                Venue.city == canonical_city(city)
            )
        return stmt

    def list(self, **filters: object) -> tuple[Sequence[Activity], int]:  # type: ignore[override]
        limit = int(filters.pop("limit", 50))  # type: ignore[arg-type]
        offset = int(filters.pop("offset", 0))  # type: ignore[arg-type]
        stmt = self._filtered(**filters)  # type: ignore[arg-type]
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        # Surface *upcoming* activities first; already-started ones sink to the
        # bottom (ordered among themselves by recency). Without this a plain
        # ``starts_at asc`` shows yesterday's events ahead of today's.
        now = datetime.now(UTC)
        started = case((Activity.starts_at >= now, 0), else_=1)
        rows = self.db.scalars(
            stmt.order_by(started.asc(), Activity.starts_at.asc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        starts_after: object | None = None,
        include_cancelled: bool = False,
        statuses: Sequence[str] = ("confirmed", "attended", "requested", "waitlisted"),
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Activity], int]:
        """Activities the given user participates in (joined or hosting)."""
        stmt = (
            select(Activity)
            .join(ActivityParticipant, ActivityParticipant.activity_id == Activity.id)
            .where(
                ActivityParticipant.user_id == user_id,
                ActivityParticipant.status.in_(list(statuses)),
            )
        )
        if not include_cancelled:
            stmt = stmt.where(Activity.is_cancelled.is_(False))
        if starts_after is not None:
            stmt = stmt.where(Activity.starts_at >= starts_after)
        total = int(self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
        rows = self.db.scalars(
            stmt.order_by(Activity.starts_at.asc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def list_mine_rows(self, user_id: uuid.UUID) -> Sequence[tuple[Activity, ActivityParticipant]]:
        """Every participation of a user (any status) paired with its activity.

        Returns the raw persisted rows so the service can derive the caller's
        real state (upcoming/waitlisted/past/hosting) and attendance outcome
        without hiding rows behind a status allow-list.
        """
        stmt = (
            select(Activity, ActivityParticipant)
            .join(ActivityParticipant, ActivityParticipant.activity_id == Activity.id)
            .where(ActivityParticipant.user_id == user_id)
            .order_by(Activity.starts_at.desc())
        )
        return list(self.db.execute(stmt).all())

    def checked_in_activity_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        """Activity ids the user has a persisted check-in row for (real history)."""
        from app.models.social import CheckIn

        rows = self.db.scalars(select(CheckIn.activity_id).where(CheckIn.user_id == user_id)).all()
        return set(rows)

    def count_by_statuses(self, activity_id: uuid.UUID, statuses: Sequence[object]) -> int:
        """How many participants currently hold one of ``statuses`` (slots in use)."""
        values = [str(s) for s in statuses]
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(ActivityParticipant)
                .where(
                    ActivityParticipant.activity_id == activity_id,
                    ActivityParticipant.status.in_(values),
                )
            )
            or 0
        )

    def participant_count(self, activity_id: uuid.UUID) -> int:
        """Confirmed/attended participants only - the real slots in use."""
        return self.count_by_statuses(activity_id, ("confirmed", "attended"))

    def waitlist_count(self, activity_id: uuid.UUID) -> int:
        return self.count_by_statuses(activity_id, ("waitlisted",))

    def get_participant(
        self, activity_id: uuid.UUID, user_id: uuid.UUID
    ) -> ActivityParticipant | None:
        return self.db.scalar(
            select(ActivityParticipant).where(
                ActivityParticipant.activity_id == activity_id,
                ActivityParticipant.user_id == user_id,
            )
        )

    def first_waitlisted(self, activity_id: uuid.UUID) -> ActivityParticipant | None:
        """The earliest waitlisted participant (FIFO by ``joined_at``)."""
        return self.db.scalar(
            select(ActivityParticipant)
            .where(
                ActivityParticipant.activity_id == activity_id,
                ActivityParticipant.status == "waitlisted",
            )
            .order_by(ActivityParticipant.joined_at.asc().nulls_last())
            .limit(1)
        )

    def list_participants(self, activity_id: uuid.UUID) -> Sequence[ActivityParticipant]:
        return self.db.scalars(
            select(ActivityParticipant)
            .where(ActivityParticipant.activity_id == activity_id)
            .order_by(ActivityParticipant.joined_at.asc().nulls_last())
        ).all()

    def add_participant(self, participant: ActivityParticipant) -> ActivityParticipant:
        self.db.add(participant)
        self.db.flush()
        return participant

    def remove_participant(self, participant: ActivityParticipant) -> None:
        self.db.delete(participant)
        self.db.flush()

    def flush(self) -> None:
        self.db.flush()
