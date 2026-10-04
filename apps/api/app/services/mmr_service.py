"""MMR rating engine (Elo) + database-integrated application service.

Two layers live here on purpose:

* **Pure functions** (``expected_score``, ``update``, ``team_average``,
  ``provisional_k_factor`` ...) - no DB, no I/O, trivially unit-testable.
* :class:`MmrService` - the DB-integrated orchestrator that turns a *verified*
  match result into rating changes, append-only history rows and a refreshed
  leaderboard.

Design rules enforced here (never trust the client):

* MMR is **sport-specific** (a user has one rating per sport slug). Only
  catalog sports flagged ``competitive=True`` may change MMR.
* Team matches use the **average team rating**; the same delta is applied to
  every member of the team.
* New players (< 10 games) use a **provisional K-factor** so their rating
  converges faster.
* Application is **idempotent**: a verified result is applied at most once
  (guarded by ``MatchResult.mmr_applied`` and a unique history row per
  ``(match_result, user)``).
* ``mmr_history`` is append-only - corrections are new rows, never updates.
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.core.sport_fields import is_competitive_sport, sport_category_slug
from app.models.activity import Activity
from app.models.enums import MatchResultStatus, NotificationType
from app.models.match import Match, MatchParticipant, MatchResult
from app.models.rating import LeaderboardEntry, MmrHistory, MmrRating
from app.services.notification_service import NotificationService

#: Default rating every player starts at.
DEFAULT_RATING = 1200.0
#: Standard K-factor once a player is established.
BASE_K = 32.0
#: K-factor while a player is still provisional (< PROVISIONAL_GAMES games).
PROVISIONAL_K = 64.0
#: Number of games after which a player stops being provisional.
PROVISIONAL_GAMES = 10
#: Elo curve width.
ELO_SCALE = 400.0


#: Prefix for the scope key of legacy (sport-less) ratings.
_LEGACY_SCOPE_PREFIX = "category:"


def mmr_scope_key(sport_slug: str | None, category: str) -> str:
    """Return the MMR scope key for a rating.

    A real sport scopes by its slug (``padel``); a legacy, sport-less row scopes
    by its activity category (``category:sports``) so back-compat rows stay
    isolated from real sports and never collide.
    """
    if sport_slug:
        return sport_slug
    return f"{_LEGACY_SCOPE_PREFIX}{category}"


# --------------------------------------------------------------------------- #
# Pure functions (no database, no I/O)                                        #
# --------------------------------------------------------------------------- #
def expected_score(r_a: float, r_b: float) -> float:
    """Return A's expected score in [0, 1] against B (Elo logistic curve).

    Equal ratings -> 0.5; a 400-point advantage -> ~0.909.
    """
    return 1.0 / (1.0 + 10.0 ** ((r_b - r_a) / ELO_SCALE))


def update(
    r_a: float, r_b: float, score_a: float, k: float = BASE_K
) -> tuple[float, float]:
    """Return ``(new_r_a, new_r_b)`` after a game with A's score in [0, 1].

    ``score_a`` is 1.0 for a win, 0.0 for a loss and 0.5 for a draw.
    """
    if not 0.0 <= score_a <= 1.0:
        raise ValueError("score_a must be between 0.0 and 1.0")
    e_a = expected_score(r_a, r_b)
    e_b = 1.0 - e_a
    score_b = 1.0 - score_a
    new_a = r_a + k * (score_a - e_a)
    new_b = r_b + k * (score_b - e_b)
    return new_a, new_b


def provisional_k_factor(
    games_played: int,
    *,
    base_k: float = BASE_K,
    provisional_k: float = PROVISIONAL_K,
    threshold: int = PROVISIONAL_GAMES,
) -> float:
    """Return the K-factor for a player with ``games_played`` games.

    Provisional players (< ``threshold`` games) swing harder to converge faster.
    """
    return provisional_k if games_played < threshold else base_k


def team_average(ratings: Sequence[float]) -> float:
    """Return the mean rating of a team (empty team -> :data:`DEFAULT_RATING`)."""
    if not ratings:
        return DEFAULT_RATING
    return sum(ratings) / len(ratings)


def team_delta(
    team_a_ratings: Sequence[float],
    team_b_ratings: Sequence[float],
    score_a: float,
    k: float = BASE_K,
) -> float:
    """Return the rating delta applied to *every* member of team A.

    Uses average team ratings against each other; team B receives ``-delta``.
    """
    r_a = team_average(team_a_ratings)
    r_b = team_average(team_b_ratings)
    e_a = expected_score(r_a, r_b)
    return k * (score_a - e_a)


def score_from_scores(team_a_score: int, team_b_score: int) -> float:
    """Map integer team scores to A's Elo score (1.0 win / 0.5 draw / 0.0 loss)."""
    if team_a_score > team_b_score:
        return 1.0
    if team_a_score < team_b_score:
        return 0.0
    return 0.5


# --------------------------------------------------------------------------- #
# Database-integrated service                                                 #
# --------------------------------------------------------------------------- #
class MmrService:
    """Applies verified match results to MMR and maintains leaderboards."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- ratings -------------------------------------------------------------
    def get_or_create_rating(
        self, user_id: uuid.UUID, sport_slug: str, category: str | None = None
    ) -> MmrRating:
        """Fetch the (user, sport) rating row, creating it at the default if absent.

        ``sport_slug`` is the scope key (see :func:`mmr_scope_key`); ``category``
        is the sport's catalog category, stored for display/back-compat.
        """
        scope = mmr_scope_key(sport_slug, category or "other")
        rating = self.db.scalar(
            select(MmrRating).where(
                MmrRating.user_id == user_id, MmrRating.sport_slug == scope
            )
        )
        if rating is None:
            rating = MmrRating(
                user_id=user_id,
                category=category or sport_category_slug(sport_slug),
                sport_slug=scope,
                rating=DEFAULT_RATING,
                games_played=0,
                wins=0,
                losses=0,
                draws=0,
            )
            self.db.add(rating)
            self.db.flush()
        return rating

    def get_user_ratings(self, user_id: uuid.UUID) -> list[MmrRating]:
        """All current ratings for a user across sports (highest first)."""
        return list(
            self.db.scalars(
                select(MmrRating)
                .where(MmrRating.user_id == user_id)
                .order_by(MmrRating.rating.desc())
            ).all()
        )

    # -- application ---------------------------------------------------------
    def apply_result(self, result: MatchResult) -> list[MmrHistory]:
        """Apply a *verified* result to every participant's MMR (idempotent).

        Returns the history rows created. If the result was already applied an
        empty list is returned and nothing is mutated.
        """
        if result.mmr_applied:
            return []
        if result.status not in (
            MatchResultStatus.VERIFIED,
            MatchResultStatus.CONFIRMED,
        ):
            raise ValidationError(
                "MMR is applied only after a result is verified or confirmed"
            )
        match = self.db.get(Match, result.match_id)
        if match is None:
            raise NotFoundError("Match not found")

        sport_slug, category = self._sport_for(match)
        if not is_competitive_sport(sport_slug):
            raise ValidationError(
                f"MMR is not tracked for non-competitive sport {sport_slug!r}"
            )

        participants = list(
            self.db.scalars(
                select(MatchParticipant).where(MatchParticipant.match_id == match.id)
            ).all()
        )
        team_a = [p for p in participants if p.team == 0]
        team_b = [p for p in participants if p.team == 1]
        if not team_a or not team_b:
            raise ValidationError("Match needs participants on both teams")

        ratings_a = [
            self.get_or_create_rating(p.user_id, sport_slug, category) for p in team_a
        ]
        ratings_b = [
            self.get_or_create_rating(p.user_id, sport_slug, category) for p in team_b
        ]

        values_a = [float(r.rating) for r in ratings_a]
        values_b = [float(r.rating) for r in ratings_b]

        score_a = score_from_scores(result.team_a_score, result.team_b_score)
        # Provisional K if anyone on either side is still provisional.
        games = [r.games_played for r in ratings_a + ratings_b]
        k = provisional_k_factor(min(games)) if games else BASE_K

        delta_a = team_delta(values_a, values_b, score_a, k)
        delta_b = -delta_a

        now = datetime.now(UTC)
        history: list[MmrHistory] = []
        for rating, delta, score in (
            [(r, delta_a, score_a) for r in ratings_a]
            + [(r, delta_b, 1.0 - score_a) for r in ratings_b]
        ):
            before = float(rating.rating)
            after = max(0.0, before + delta)
            applied = after - before
            rating.rating = after
            rating.games_played += 1
            if score == 1.0:
                rating.wins += 1
            elif score == 0.0:
                rating.losses += 1
            else:
                rating.draws += 1
            row = MmrHistory(
                rating_id=rating.id,
                user_id=rating.user_id,
                match_result_id=result.id,
                rating_before=before,
                rating_after=after,
                delta=applied,
                reason="match",
            )
            self.db.add(row)
            history.append(row)

        result.mmr_applied = True
        result.verified_at = now
        self.db.flush()

        self._notify(participants, sport_slug, category, delta_a, delta_b)
        self.recompute_leaderboard(sport_slug, category)
        return history

    def _sport_for(self, match: Match) -> tuple[str | None, str]:
        """Resolve a match's ``(sport_slug, category)``.

        The sport comes from the match's activity (or its tournament); legacy
        activities without a sport return ``(None, <activity category>)`` so they
        scope under the back-compat ``category:<cat>`` key.
        """
        if match.activity_id is not None:
            activity = self.db.get(Activity, match.activity_id)
            if activity is not None:
                slug = getattr(activity, "sport_slug", None)
                if slug:
                    return str(slug), sport_category_slug(str(slug))
                return None, str(activity.category)
        return None, "other"

    def _notify(
        self,
        participants: Sequence[MatchParticipant],
        sport_slug: str | None,
        category: str,
        delta_a: float,
        delta_b: float,
    ) -> None:
        svc = NotificationService(self.db)
        label = sport_slug or category
        for p in participants:
            delta = delta_a if p.team == 0 else delta_b
            sign = "+" if delta >= 0 else ""
            svc.notify(
                p.user_id,
                type=NotificationType.MMR_UPDATE,
                title="MMR updated",
                body=f"Your {label} rating changed by {sign}{delta:.1f}.",
                data={
                    "sport_slug": sport_slug,
                    "category": category,
                    "delta": round(delta, 2),
                },
                commit=False,
            )

    # -- leaderboard ---------------------------------------------------------
    def _leaderboard_scope(self, sport_slug: str | None, category: str) -> str:
        """The rating scope key a leaderboard is built from."""
        return mmr_scope_key(sport_slug, category)

    def _ranked_ratings(self, scope: str) -> list[MmrRating]:
        """All *ranked* ratings for a scope (>= 1 verified game), best first."""
        return list(
            self.db.scalars(
                select(MmrRating)
                .where(
                    MmrRating.sport_slug == scope,
                    MmrRating.games_played >= 1,
                )
                .order_by(MmrRating.rating.desc(), MmrRating.games_played.desc())
            ).all()
        )

    def recompute_leaderboard(
        self,
        sport_slug: str | None,
        category: str,
        period: str = "all_time",
    ) -> list[LeaderboardEntry]:
        """Rebuild the ranked leaderboard for a *sport* scope from current ratings.

        Only players with at least one verified match in that sport are ranked;
        players with none are UNRANKED (see :meth:`get_standing`).
        """
        scope = self._leaderboard_scope(sport_slug, category)
        ratings = self._ranked_ratings(scope)
        # Drop stale rows, then rewrite a fresh, correctly-ranked snapshot.
        self.db.execute(
            delete(LeaderboardEntry).where(
                LeaderboardEntry.sport_slug == scope,
                LeaderboardEntry.period == period,
            )
        )
        now = datetime.now(UTC)
        entries: list[LeaderboardEntry] = []
        for rank, rating in enumerate(ratings, start=1):
            entry = LeaderboardEntry(
                user_id=rating.user_id,
                category=category,
                sport_slug=scope,
                period=period,
                rank=rank,
                rating=float(rating.rating),
                games_played=rating.games_played,
                computed_at=now,
            )
            self.db.add(entry)
            entries.append(entry)
        self.db.flush()
        return entries

    def get_leaderboard(
        self,
        sport_slug: str | None,
        category: str,
        period: str = "all_time",
        limit: int = 50,
    ) -> list[LeaderboardEntry]:
        """Return the materialised sport leaderboard (recomputing if empty)."""
        scope = self._leaderboard_scope(sport_slug, category)
        rows = list(
            self.db.scalars(
                select(LeaderboardEntry)
                .where(
                    LeaderboardEntry.sport_slug == scope,
                    LeaderboardEntry.period == period,
                )
                .order_by(LeaderboardEntry.rank.asc())
                .limit(limit)
            ).all()
        )
        if not rows:
            self.recompute_leaderboard(sport_slug, category, period)
            rows = list(
                self.db.scalars(
                    select(LeaderboardEntry)
                    .where(
                        LeaderboardEntry.sport_slug == scope,
                        LeaderboardEntry.period == period,
                    )
                    .order_by(LeaderboardEntry.rank.asc())
                    .limit(limit)
                ).all()
            )
        return rows

    def get_standing(
        self,
        user_id: uuid.UUID,
        sport_slug: str | None,
        category: str,
        period: str = "all_time",
    ) -> dict[str, object]:
        """A user's standing in a sport leaderboard.

        Returns ``ranked=True`` with ``rank``/``rating``/``games_played`` when the
        user has at least one verified match in that sport; otherwise
        ``ranked=False`` with ``rank=None`` (the **UNRANKED** state).
        """
        scope = self._leaderboard_scope(sport_slug, category)
        rating = self.db.scalar(
            select(MmrRating).where(
                MmrRating.user_id == user_id,
                MmrRating.sport_slug == scope,
            )
        )
        if rating is None or rating.games_played < 1:
            return {
                "user_id": user_id,
                "sport_slug": scope,
                "ranked": False,
                "rank": None,
                "rating": None,
                "games_played": 0 if rating is None else rating.games_played,
            }
        rank = (
            self.db.scalar(
                select(func.count())
                .select_from(MmrRating)
                .where(
                    MmrRating.sport_slug == scope,
                    MmrRating.games_played >= 1,
                    MmrRating.rating > rating.rating,
                )
            )
            or 0
        ) + 1
        return {
            "user_id": user_id,
            "sport_slug": scope,
            "ranked": True,
            "rank": int(rank),
            "rating": float(rating.rating),
            "games_played": rating.games_played,
        }

    def history_for_user(
        self, user_id: uuid.UUID, limit: int = 50
    ) -> list[MmrHistory]:
        """Append-only rating history for a user (newest first)."""
        return list(
            self.db.scalars(
                select(MmrHistory)
                .where(MmrHistory.user_id == user_id)
                .order_by(MmrHistory.created_at.desc())
                .limit(limit)
            ).all()
        )
