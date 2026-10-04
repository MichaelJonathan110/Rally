"""Activity business logic.

Owns the rules for creating sport-specific activities (sport validation, capacity,
venue resource), joining and leaving (real capacity + waitlist state machine) and
listing/filtering. Routers call these methods; the service never touches HTTP.

Membership state machine
------------------------
* joining an activity with a free slot  -> ``CONFIRMED``
* joining an activity that is full       -> ``WAITLISTED`` (never an error)
* leaving frees the slot and PROMOTES the earliest waitlisted participant to
  ``CONFIRMED`` - so the waitlist is real, persisted state, not a UI label.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.core.sport_fields import SportFieldError, resolve_sport_fields
from app.core.sports import SPORT_BY_SLUG
from app.models.activity import Activity, ActivityCategoryLink, ActivityParticipant
from app.models.enums import ActivityVisibility, ParticipantStatus
from app.models.venue import VenueCourt
from app.repositories.activity import ActivityRepository

#: Statuses that occupy a capacity slot.
_ACTIVE_STATUSES = (ParticipantStatus.CONFIRMED, ParticipantStatus.ATTENDED)
#: Statuses that are on the waitlist, ordered FIFO by ``joined_at``.
_WAITLIST_STATUSES = (ParticipantStatus.WAITLISTED,)


#: The four real states a caller's activity can be in ("Aktivitas Saya").
MINE_STATES = ("upcoming", "waitlisted", "past", "hosting")


@dataclass(frozen=True)
class MyActivityEntry:
    """A caller-scoped activity row: the ORM activity plus derived view fields.

    Plain data (no Pydantic) so the service layer stays HTTP/schema-free; the
    router maps this onto :class:`app.schemas.activity.MyActivityRead`.
    """

    activity: Activity
    state: str
    participation_status: ParticipantStatus
    is_host: bool
    attendance: str | None
    sport_label: str | None
    sport_label_en: str | None
    venue_label: str | None
    court_label: str | None


class ActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ActivityRepository(db)

    # -- reads ---------------------------------------------------------------
    def get(self, activity_id: uuid.UUID) -> Activity:
        activity = self.repo.get(activity_id)
        if activity is None:
            raise NotFoundError("Activity not found")
        return activity

    def list_activities(
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
        starts_after: datetime | None = None,
        starts_before: datetime | None = None,
        search: str | None = None,
        include_cancelled: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Activity], int]:
        rows, total = self.repo.list(
            category=category,
            sport_slug=sport_slug,
            sport_category=sport_category,
            activity_type=activity_type,
            skill_level=skill_level,
            city=city,
            venue_id=venue_id,
            host_id=host_id,
            starts_after=starts_after,
            starts_before=starts_before,
            search=search,
            include_cancelled=include_cancelled,
            limit=limit,
            offset=offset,
        )
        return list(rows), total

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        starts_after: datetime | None = None,
        include_cancelled: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Activity], int]:
        """Activities the user has joined or is hosting (the "Aktivitas Saya" rail)."""
        rows, total = self.repo.list_for_user(
            user_id,
            starts_after=starts_after,
            include_cancelled=include_cancelled,
            limit=limit,
            offset=offset,
        )
        return list(rows), total

    def list_mine(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        sport: str | None = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MyActivityEntry], int, dict[str, list[MyActivityEntry]]]:
        """The caller's own activities, split by real persisted state.

        Every row is derived from the caller's :class:`ActivityParticipant` rows
        (never a stub) plus their persisted :class:`CheckIn` rows for attendance.
        Buckets (mutually exclusive, host-first):

        * ``past``       - cancelled activity, cancelled/declined participation,
          a terminal attendance outcome (attended/no_show), or an activity whose
          end time has passed.
        * ``hosting``    - the caller created (hosts) the activity.
        * ``waitlisted`` - the caller holds a real ``waitlisted`` slot.
        * ``upcoming``   - everything else (joined/confirmed, still in the future).

        Returns ``(page_items, total, groups)`` where ``groups`` is the full
        (sport-filtered) partition so a client can render all four rails, while
        ``items``/``total`` additionally honour the ``status`` and
        ``active_only`` filters and page (``active_only`` drops past items so a
        caller with no upcoming/ongoing registration gets an empty page).
        """
        now = datetime.now(UTC)
        checked_in = self.repo.checked_in_activity_ids(user_id)

        entries: list[MyActivityEntry] = [
            self._mine_entry(activity, participant, user_id, checked_in, now)
            for activity, participant in self.repo.list_mine_rows(user_id)
        ]

        if sport:
            entries = [e for e in entries if e.activity.sport_slug == sport]

        groups: dict[str, list[MyActivityEntry]] = {name: [] for name in MINE_STATES}
        for entry in entries:
            groups.setdefault(entry.state, []).append(entry)
        for bucket in groups.values():
            bucket.sort(key=lambda e: self._mine_sort_key(e))

        flat = [e for e in entries if e.state == status] if status else entries
        # The flat page feeds "Aktivitas Saya" rails: upcoming/ongoing items must
        # lead (soonest first) so stale *past* activities never surface at the
        # top; past items only trail, most-recent first.
        if active_only:
            # Drop anything that has already finished so a caller with no
            # upcoming/ongoing registration sees an empty state, never history.
            flat = [e for e in flat if e.state != "past"]
        flat = sorted(flat, key=self._mine_flat_key)
        total = len(flat)
        page = flat[offset : offset + limit]
        return page, total, groups

    @staticmethod
    def _mine_flat_key(entry: MyActivityEntry) -> tuple[int, float]:
        """Order the flat "Aktivitas Saya" page: active first, past last.

        ``upcoming``/``hosting``/``waitlisted`` rank ahead of ``past``; active
        items are soonest-first and past items are most-recent-first.
        """
        starts = entry.activity.starts_at
        if starts is not None and starts.tzinfo is None:
            starts = starts.replace(tzinfo=UTC)
        ts = starts.timestamp() if starts is not None else 0.0
        if entry.state == "past":
            return (2, -ts)
        if entry.state == "waitlisted":
            return (1, ts)
        return (0, ts)  # upcoming + hosting, soonest first

    @staticmethod
    def _mine_sort_key(entry: MyActivityEntry) -> tuple[int, float]:
        """Soonest upcoming first; most recent past first."""
        starts = entry.activity.starts_at
        if starts is not None and starts.tzinfo is None:
            starts = starts.replace(tzinfo=UTC)
        ts = starts.timestamp() if starts is not None else 0.0
        if entry.state == "past":
            return (0, -ts)  # most recent past first
        return (1, ts)  # active items (upcoming/hosting/waitlisted) soonest first

    def _mine_entry(
        self,
        activity: Activity,
        participant: ActivityParticipant,
        user_id: uuid.UUID,
        checked_in: set[uuid.UUID],
        now: datetime,
    ) -> MyActivityEntry:
        """Derive one caller-scoped entry from persisted rows (real state)."""
        is_host = bool(participant.is_host) or activity.host_id == user_id
        pstatus = participant.status

        starts = activity.starts_at
        if starts is not None and starts.tzinfo is None:
            starts = starts.replace(tzinfo=UTC)
        ends = activity.ends_at
        if ends is not None and ends.tzinfo is None:
            ends = ends.replace(tzinfo=UTC)
        effective_end = ends if ends is not None else starts

        state = "upcoming"
        attendance: str | None = None
        # "past" is driven by the END time, not the start, so an ongoing event
        # still leads the rails ("upcoming/ongoing first"). Terminal
        # participation/attendance outcomes win first; then a FINISHED event is
        # past regardless of whether the caller hosts or merely joined it - this
        # is what stops stale *hosted* history from leading "Aktivitas Saya".
        finished = effective_end is not None and effective_end < now
        if activity.is_cancelled:
            state, attendance = "past", "cancelled"
        elif pstatus in (ParticipantStatus.CANCELLED, ParticipantStatus.DECLINED):
            state, attendance = "past", str(pstatus)
        elif pstatus == ParticipantStatus.NO_SHOW:
            state, attendance = "past", "no_show"
        elif pstatus == ParticipantStatus.ATTENDED:
            state, attendance = "past", "attended"
        elif finished:
            state = "past"
            attendance = "attended" if activity.id in checked_in else "no_show"
        elif is_host:
            state = "hosting"
        elif pstatus == ParticipantStatus.WAITLISTED:
            state = "waitlisted"

        sport_row = SPORT_BY_SLUG.get(activity.sport_slug) if activity.sport_slug else None
        venue = activity.venue
        court_label = None
        if activity.venue_court_id is not None:
            court = self.db.get(VenueCourt, activity.venue_court_id)
            court_label = court.name if court is not None else None

        return MyActivityEntry(
            activity=activity,
            state=state,
            participation_status=pstatus,
            is_host=is_host,
            attendance=attendance,
            sport_label=str(sport_row["label_id"]) if sport_row else None,
            sport_label_en=str(sport_row["label_en"]) if sport_row else None,
            venue_label=venue.name if venue is not None else None,
            court_label=court_label,
        )

    def participant_count(self, activity_id: uuid.UUID) -> int:
        """Confirmed participants only (slots in use)."""
        return self.repo.participant_count(activity_id)

    def waitlist_count(self, activity_id: uuid.UUID) -> int:
        return self.repo.waitlist_count(activity_id)

    def list_participants(self, activity_id: uuid.UUID) -> list[ActivityParticipant]:
        self.get(activity_id)  # 404 if missing
        return list(self.repo.list_participants(activity_id))

    # -- writes --------------------------------------------------------------
    def create(self, host_id: uuid.UUID, data: dict) -> Activity:
        data = dict(data)
        category_link_id = data.pop("category_link_id", None)
        if category_link_id is not None:
            link = self.db.get(ActivityCategoryLink, category_link_id)
            if link is None:
                raise ValidationError("Unknown category_link_id")

        # Validate/resolve sport-specific fields against the sports catalog and
        # flatten them onto the model columns.
        try:
            resolved = resolve_sport_fields(
                sport_slug=data.get("sport_slug"),
                variant=data.get("sport_variant"),
                format=data.get("sport_format"),
                metrics=data.get("sport_metrics"),
            )
        except SportFieldError as exc:
            raise ValidationError(str(exc)) from exc
        if resolved:
            data["sport_slug"] = resolved["sport_slug"]
            data["sport_category"] = resolved["sport_category"]
            data["sport_metrics"] = resolved["metrics"]
        else:
            # No sport: nothing sport-specific may be set.
            data.pop("sport_slug", None)
            data.pop("sport_metrics", None)

        starts_at = data.get("starts_at")
        ends_at = data.get("ends_at")
        if ends_at is not None and starts_at is not None and ends_at <= starts_at:
            raise ValidationError("ends_at must be after starts_at")

        activity = Activity(host_id=host_id, category_link_id=category_link_id, **data)
        self.repo.add(activity)
        # The host is automatically a confirmed participant (occupies a slot).
        self.repo.add_participant(
            ActivityParticipant(
                activity_id=activity.id,
                user_id=host_id,
                status=ParticipantStatus.CONFIRMED,
                is_host=True,
                joined_at=datetime.now(UTC),
            )
        )
        self.repo.commit()
        self.repo.refresh(activity)
        return activity

    def update(self, activity_id: uuid.UUID, actor_id: uuid.UUID, data: dict) -> Activity:
        activity = self.get(activity_id)
        if activity.host_id != actor_id:
            raise PermissionDeniedError("Only the host may modify this activity")
        data = dict(data)

        # Re-validate sport fields if the sport or its sub-fields are changing.
        if any(k in data for k in ("sport_slug", "sport_variant", "sport_format", "sport_metrics")):
            try:
                resolved = resolve_sport_fields(
                    sport_slug=data.get("sport_slug", activity.sport_slug),
                    variant=data.get("sport_variant", activity.sport_variant),
                    format=data.get("sport_format", activity.sport_format),
                    metrics=data.get("sport_metrics", activity.sport_metrics),
                )
            except SportFieldError as exc:
                raise ValidationError(str(exc)) from exc
            if resolved:
                data["sport_slug"] = resolved["sport_slug"]
                data["sport_category"] = resolved["sport_category"]
                data["sport_metrics"] = resolved["metrics"]
            else:
                data["sport_slug"] = None
                data["sport_category"] = None
                data["sport_metrics"] = None

        for key, value in data.items():
            if value is not None:
                setattr(activity, key, value)
        if activity.ends_at is not None and activity.ends_at <= activity.starts_at:
            raise ValidationError("ends_at must be after starts_at")
        self.repo.commit()
        self.repo.refresh(activity)
        return activity

    def cancel(self, activity_id: uuid.UUID, actor_id: uuid.UUID) -> Activity:
        """Cancel an activity (host only). Idempotent for an already-cancelled row."""
        activity = self.get(activity_id)
        if activity.host_id != actor_id:
            raise PermissionDeniedError("Only the host may cancel this activity")
        if not activity.is_cancelled:
            activity.is_cancelled = True
            self.repo.commit()
            self.repo.refresh(activity)
        return activity

    def refresh(self, activity: Activity) -> Activity:
        return self.repo.refresh(activity)

    def delete(self, activity_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        activity = self.get(activity_id)
        if activity.host_id != actor_id:
            raise PermissionDeniedError("Only the host may delete this activity")
        self.repo.delete(activity)
        self.repo.commit()

    # -- membership ----------------------------------------------------------
    def join(self, activity_id: uuid.UUID, user_id: uuid.UUID) -> ActivityParticipant:
        """Join an activity, or waitlist when it is full.

        * free slot -> ``CONFIRMED``
        * full       -> ``WAITLISTED`` (persisted, FIFO by ``joined_at``)

        Re-joining after leaving/cancelling restores the participant.
        """
        activity = self.get(activity_id)
        if activity.is_cancelled:
            raise ValidationError("Activity is cancelled")
        if activity.visibility == ActivityVisibility.PRIVATE:
            # Private activities are invite-only; only the host may add people.
            raise PermissionDeniedError("This activity is private (invite only)")

        existing = self.repo.get_participant(activity_id, user_id)
        if existing is not None and existing.status not in (
            ParticipantStatus.CANCELLED,
            ParticipantStatus.DECLINED,
        ):
            raise ConflictError("You have already joined this activity")

        now = datetime.now(UTC)
        confirmed = self.repo.count_by_statuses(activity_id, _ACTIVE_STATUSES)
        if confirmed >= activity.max_participants:
            new_status = ParticipantStatus.WAITLISTED
        else:
            new_status = ParticipantStatus.CONFIRMED

        if existing is not None:  # re-joining after leaving
            existing.status = new_status
            existing.joined_at = now
            participant = existing
        else:
            participant = ActivityParticipant(
                activity_id=activity_id,
                user_id=user_id,
                status=new_status,
                is_host=False,
                joined_at=now,
            )
            self.repo.add_participant(participant)
        self.repo.commit()
        self.repo.refresh(participant)
        return participant

    def leave(self, activity_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Leave an activity, freeing a slot and promoting the next waiter.

        Leaving frees the participant's slot; the earliest waitlisted participant
        (FIFO by ``joined_at``) is promoted to ``CONFIRMED`` - real, persisted
        state change.
        """
        self.get(activity_id)
        participant = self.repo.get_participant(activity_id, user_id)
        if participant is None or participant.status == ParticipantStatus.CANCELLED:
            raise NotFoundError("You are not a participant of this activity")
        if participant.is_host:
            raise ValidationError("The host cannot leave their own activity")

        was_confirmed = participant.status in _ACTIVE_STATUSES
        self.repo.remove_participant(participant)
        if was_confirmed:
            self._promote_next_waiter(activity_id)
        self.repo.commit()

    def _promote_next_waiter(self, activity_id: uuid.UUID) -> None:
        """Promote the earliest waitlisted participant to CONFIRMED (FIFO)."""
        waiter = self.repo.first_waitlisted(activity_id)
        if waiter is not None:
            waiter.status = ParticipantStatus.CONFIRMED
            waiter.joined_at = datetime.now(UTC)
            self.repo.flush()
