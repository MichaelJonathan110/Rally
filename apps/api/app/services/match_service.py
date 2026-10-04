"""Match lifecycle + result verification business logic.

Flow enforced server-side (never trusted to the client):

1. **Create** (host only) - the host records a match on an activity, naming the
   participants and their teams. Every participant must already be a participant
   of that activity.
2. **Submit result** - a listed participant submits the final score. The result
   starts in ``SUBMITTED`` (*pending verification*).
3. **Verify** - only *listed participants* (never the submitter) may confirm or
   dispute. When a majority confirm, the result becomes ``VERIFIED``, the match
   is ``COMPLETED`` and MMR is applied exactly once. A dispute blocks MMR.
"""
from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.sport_fields import is_competitive_sport
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.activity import Activity, ActivityParticipant
from app.models.enums import (
    MatchResultStatus,
    MatchStatus,
    NotificationType,
    ParticipantStatus,
)
from app.models.match import Match, MatchParticipant, MatchResult, ResultVerification
from app.services.mmr_service import MmrService
from app.services.notification_service import NotificationService

#: Result states that mean "a live result is already on file for this match".
_ACTIVE_RESULTS = (MatchResultStatus.SUBMITTED, MatchResultStatus.VERIFIED)


class MatchService:
    """Coordinates match creation, result submission and verification."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- reads ---------------------------------------------------------------
    def get(self, match_id: uuid.UUID) -> Match:
        match = self.db.get(Match, match_id)
        if match is None:
            raise NotFoundError("Match not found")
        return match

    def get_result(self, result_id: uuid.UUID) -> MatchResult:
        result = self.db.get(MatchResult, result_id)
        if result is None:
            raise NotFoundError("Match result not found")
        return result

    def _participant_ids(self, match: Match) -> set[uuid.UUID]:
        return {p.user_id for p in match.participants}

    # -- create --------------------------------------------------------------
    def create_match(
        self,
        activity_id: uuid.UUID,
        host_id: uuid.UUID,
        participants: list[dict],
        scheduled_at: datetime | None = None,
    ) -> Match:
        """Host records a match with its participants (RBAC: host only)."""
        activity = self.db.get(Activity, activity_id)
        if activity is None:
            raise NotFoundError("Activity not found")
        if activity.host_id != host_id:
            raise PermissionDeniedError("Only the host may record a match")
        if activity.is_cancelled:
            raise ValidationError("Activity is cancelled")

        if len(participants) < 2:
            raise ValidationError("A match needs at least two participants")

        user_ids = [p["user_id"] for p in participants]
        if len(set(user_ids)) != len(user_ids):
            raise ValidationError("Duplicate participants in match")

        if {p.get("team", 0) for p in participants} != {0, 1}:
            raise ValidationError("Match must have participants on both teams")

        # Every listed player must already belong to the activity.
        confirmed = {
            row.user_id
            for row in self.db.scalars(
                select(ActivityParticipant).where(
                    ActivityParticipant.activity_id == activity_id,
                    ActivityParticipant.status != ParticipantStatus.CANCELLED,
                )
            ).all()
        }
        if any(uid not in confirmed for uid in user_ids):
            raise ValidationError(
                "All match participants must be activity participants"
            )

        match = Match(
            activity_id=activity_id,
            status=MatchStatus.IN_PROGRESS,
            scheduled_at=scheduled_at,
            played_at=datetime.now(UTC),
        )
        self.db.add(match)
        self.db.flush()

        for p in participants:
            self.db.add(
                MatchParticipant(
                    match_id=match.id,
                    user_id=p["user_id"],
                    team=p.get("team", 0),
                    score=p.get("score", 0),
                )
            )
        self.db.commit()
        self.db.refresh(match)
        return match

    # -- submit result -------------------------------------------------------
    def submit_result(
        self,
        match_id: uuid.UUID,
        submitter_id: uuid.UUID,
        team_a_score: int,
        team_b_score: int,
        notes: str | None = None,
    ) -> MatchResult:
        """Submit a final score; the result enters PENDING_VERIFICATION."""
        match = self.get(match_id)
        if match.status == MatchStatus.CANCELLED:
            raise ValidationError("Match is cancelled")

        allowed = self._participant_ids(match)
        if submitter_id not in allowed:
            raise PermissionDeniedError("Only match participants may submit a result")

        existing = self.db.scalar(
            select(MatchResult)
            .where(MatchResult.match_id == match_id)
            .order_by(MatchResult.created_at.desc())
        )
        if existing is not None and existing.status in _ACTIVE_RESULTS:
            raise ConflictError("A result has already been submitted for this match")

        winner = None
        if team_a_score > team_b_score:
            winner = 0
        elif team_b_score > team_a_score:
            winner = 1

        result = MatchResult(
            match_id=match_id,
            submitted_by_id=submitter_id,
            status=MatchResultStatus.SUBMITTED,
            team_a_score=team_a_score,
            team_b_score=team_b_score,
            winner_team=winner,
            notes=notes,
            mmr_applied=False,
        )
        self.db.add(result)
        match.status = MatchStatus.IN_PROGRESS
        self.db.flush()

        others = [uid for uid in allowed if uid != submitter_id]
        NotificationService(self.db).notify_many(
            others,
            type=NotificationType.MATCH_RESULT,
            title="Confirm the match result",
            body="A result was submitted for your match - confirm or dispute it.",
            data={"match_id": str(match_id), "result_id": str(result.id)},
            commit=False,
        )
        self.db.commit()
        self.db.refresh(result)
        return result

    # -- verify --------------------------------------------------------------
    def needed_confirmations(self, match: Match) -> int:
        """Majority of the *other* participants (excluding the submitter)."""
        total = len(self._participant_ids(match))
        return max(1, math.ceil((total - 1) / 2))

    def verify_result(
        self,
        match_id: uuid.UUID,
        result_id: uuid.UUID,
        verifier_id: uuid.UUID,
        confirmed: bool = True,
        comment: str | None = None,
    ) -> MatchResult:
        """A listed participant confirms or disputes a submitted result.

        On a majority confirm the result becomes VERIFIED, the match COMPLETED
        and MMR is applied exactly once. A dispute blocks MMR.
        """
        match = self.get(match_id)
        result = self.get_result(result_id)
        if result.match_id != match_id:
            raise ValidationError("Result does not belong to this match")

        allowed = self._participant_ids(match)
        if verifier_id not in allowed:
            raise PermissionDeniedError("Only listed participants may verify")
        if verifier_id == result.submitted_by_id:
            raise PermissionDeniedError("The submitter cannot verify their own result")

        if result.status == MatchResultStatus.VERIFIED:
            raise ConflictError("Result already verified")
        if result.status == MatchResultStatus.DISPUTED and confirmed:
            raise ConflictError("Result was disputed and cannot be confirmed")

        existing = self.db.scalar(
            select(ResultVerification).where(
                ResultVerification.result_id == result_id,
                ResultVerification.user_id == verifier_id,
            )
        )
        if existing is not None:
            raise ConflictError("You have already responded to this result")

        self.db.add(
            ResultVerification(
                result_id=result_id,
                user_id=verifier_id,
                confirmed=confirmed,
                disputed=not confirmed,
                comment=comment,
            )
        )
        self.db.flush()

        if not confirmed:
            result.status = MatchResultStatus.DISPUTED
            match.status = MatchStatus.DISPUTED
            NotificationService(self.db).notify(
                result.submitted_by_id,
                type=NotificationType.MATCH_RESULT,
                title="Match result disputed",
                body="A participant disputed your submitted result.",
                data={"match_id": str(match_id), "result_id": str(result_id)},
                commit=False,
            )
            self.db.commit()
            self.db.refresh(result)
            return result

        confirmations = int(
            self.db.scalar(
                select(func.count())
                .select_from(ResultVerification)
                .where(
                    ResultVerification.result_id == result_id,
                    ResultVerification.confirmed.is_(True),
                )
            )
            or 0
        )
        if confirmations >= self.needed_confirmations(match):
            self._finalize(match, result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def _finalize(self, match: Match, result: MatchResult) -> None:
        """Mark verified + completed and apply MMR exactly once."""
        result.status = MatchResultStatus.VERIFIED
        result.verified_at = datetime.now(UTC)
        match.status = MatchStatus.COMPLETED
        if result.winner_team is not None:
            for p in match.participants:
                p.is_winner = p.team == result.winner_team
        # MMR is applied only for competitive sports; a verified result in a
        # non-competitive sport (e.g. hiking) is still final, just unranked.
        if not result.mmr_applied and self._match_is_competitive(match):
            MmrService(self.db).apply_result(result)

    def _match_is_competitive(self, match: Match) -> bool:
        """True when the match's sport is flagged ``competitive`` in the catalog."""
        if match.activity_id is None:
            return False
        activity = self.db.get(Activity, match.activity_id)
        if activity is None:
            return False
        return is_competitive_sport(getattr(activity, "sport_slug", None))
