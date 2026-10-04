"""Check-in business logic.

A participant may check in to an activity only inside its check-in window
(opens a configurable lead time before the start and closes at the end, or a
default duration later). Check-ins are idempotent per (activity, user): a repeat
call returns the existing row instead of creating a duplicate.

Check-in is also the point where attendance is *persisted*: a successful check-in
moves the participant row from ``CONFIRMED`` to ``ATTENDED`` and credits the
user's ``Profile.reputation_score``. The host may later mark a participant as
``NO_SHOW``, which debits reputation. Both transitions are idempotent - applying
them twice never double-counts reputation.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.activity import Activity, ActivityParticipant
from app.models.enums import ParticipantStatus
from app.models.social import CheckIn
from app.models.user import Profile

#: How early a participant may check in before the activity starts.
CHECKIN_OPENS_BEFORE = timedelta(minutes=60)
#: Fallback activity length when ``ends_at`` is unset.
DEFAULT_ACTIVITY_DURATION = timedelta(hours=4)

#: Reputation awarded when a participant actually attends (checks in).
REP_ATTENDED_DELTA = 2
#: Reputation debited when the host marks a confirmed participant as a no-show.
REP_NO_SHOW_DELTA = -3


class CheckInService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _window(activity: Activity) -> tuple[datetime, datetime]:
        starts_at = activity.starts_at
        if starts_at.tzinfo is None:
            starts_at = starts_at.replace(tzinfo=UTC)
        ends_at = activity.ends_at
        if ends_at is None:
            ends_at = starts_at + DEFAULT_ACTIVITY_DURATION
        elif ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=UTC)
        return starts_at - CHECKIN_OPENS_BEFORE, ends_at

    def _get_participant(
        self, activity_id: uuid.UUID, user_id: uuid.UUID
    ) -> ActivityParticipant | None:
        return self.db.scalar(
            select(ActivityParticipant).where(
                ActivityParticipant.activity_id == activity_id,
                ActivityParticipant.user_id == user_id,
            )
        )

    def _require_participant(self, activity_id: uuid.UUID, user_id: uuid.UUID) -> ActivityParticipant:
        """Return the participant row, or raise unless they are ``CONFIRMED``.

        Only a ``CONFIRMED`` participant may check in. Missing rows, waitlisted
        and cancelled (or otherwise non-confirmed) participants are rejected.
        """
        participant = self._get_participant(activity_id, user_id)
        if participant is None:
            raise PermissionDeniedError("Only participants may check in to this activity")
        if participant.status != ParticipantStatus.CONFIRMED:
            raise PermissionDeniedError(
                "Only confirmed participants may check in to this activity "
                f"(current status: {participant.status.value})"
            )
        return participant

    def _adjust_reputation(self, user_id: uuid.UUID, delta: int) -> None:
        """Apply ``delta`` to the user's reputation in the current transaction.

        Called in the same transaction as the attendance status change so the
        two never diverge.
        """
        profile = self.db.scalar(select(Profile).where(Profile.user_id == user_id))
        if profile is None:
            return
        profile.reputation_score = (profile.reputation_score or 0) + delta

    # -- reads ---------------------------------------------------------------
    def list_checkins(self, activity_id: uuid.UUID) -> list[CheckIn]:
        return list(
            self.db.scalars(
                select(CheckIn)
                .where(CheckIn.activity_id == activity_id)
                .order_by(CheckIn.checked_in_at.asc().nulls_last())
            ).all()
        )

    # -- writes --------------------------------------------------------------
    def check_in(
        self,
        activity_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        method: str = "manual",
        now: datetime | None = None,
    ) -> CheckIn:
        activity = self.db.get(Activity, activity_id)
        if activity is None:
            raise NotFoundError("Activity not found")
        if activity.is_cancelled:
            raise ValidationError("Activity is cancelled")

        existing = self.db.scalar(
            select(CheckIn).where(
                CheckIn.activity_id == activity_id, CheckIn.user_id == user_id
            )
        )
        if existing is not None:
            return existing  # idempotent - never double-applies reputation

        # Not checked in yet: only a CONFIRMED participant may proceed.
        participant = self._require_participant(activity_id, user_id)

        moment = now or datetime.now(UTC)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        opens_at, closes_at = self._window(activity)
        if moment < opens_at:
            raise ConflictError("Check-in has not opened yet for this activity")
        if moment > closes_at:
            raise ConflictError("Check-in window has closed for this activity")

        checkin = CheckIn(
            activity_id=activity_id,
            user_id=user_id,
            checked_in_at=moment,
            latitude=latitude,
            longitude=longitude,
            method=method,
        )
        self.db.add(checkin)
        # Persist attendance and credit reputation atomically with the check-in.
        participant.status = ParticipantStatus.ATTENDED
        self._adjust_reputation(user_id, REP_ATTENDED_DELTA)
        self.db.commit()
        self.db.refresh(checkin)
        return checkin

    def mark_no_show(
        self,
        activity_id: uuid.UUID,
        user_id: uuid.UUID,
        actor: uuid.UUID,
    ) -> ActivityParticipant:
        """Host-only: mark a participant as ``NO_SHOW`` after the activity.

        Sets ``status = NO_SHOW`` and debits the participant's reputation. It is
        idempotent - marking an already-``NO_SHOW`` participant is a no-op and
        never double-debits.
        """
        activity = self.db.get(Activity, activity_id)
        if activity is None:
            raise NotFoundError("Activity not found")
        if actor != activity.host_id:
            raise PermissionDeniedError("Only the host may mark a participant as no-show")

        participant = self._get_participant(activity_id, user_id)
        if participant is None:
            raise NotFoundError("Participant not found for this activity")
        if participant.status == ParticipantStatus.NO_SHOW:
            return participant  # idempotent - never double-debits

        participant.status = ParticipantStatus.NO_SHOW
        self._adjust_reputation(user_id, REP_NO_SHOW_DELTA)
        self.db.commit()
        self.db.refresh(participant)
        return participant
