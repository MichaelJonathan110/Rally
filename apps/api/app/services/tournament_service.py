"""Tournament business logic: entries, single-elimination bracket, standings.

The bracket engine is deterministic: given an ordered list of entries it lays
out a standard seeded single-elimination bracket, auto-advances byes, and
advances winners into the next round as results are recorded. All mutation goes
through the repository so the service stays HTTP-free.
"""
from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.models.enums import TournamentFormat, TournamentStatus, UserRole
from app.models.tournament import Tournament, TournamentEntry, TournamentMatch
from app.repositories.tournament import TournamentRepository


def _slugify(value: str) -> str:
    out = []
    for ch in value.lower().strip():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_/":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80] or "tournament"


def _bracket_seed_order(size: int) -> list[int]:
    """Standard bracket seeding: 1-based seed numbers in slot order.

    For size 8 -> [1, 8, 4, 5, 2, 7, 3, 6] so seed 1 meets seed 8 first and the
    strongest seeds are kept apart until the later rounds.
    """
    order = [1, 2]
    while len(order) < size:
        n = len(order) * 2
        new: list[int] = []
        for x in order:
            new.append(x)
            new.append(n + 1 - x)
        order = new
    return order


class TournamentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TournamentRepository(db)

    # -- tournaments ---------------------------------------------------------
    def get(self, tournament_id: uuid.UUID) -> Tournament:
        t = self.repo.get(tournament_id)
        if t is None:
            raise NotFoundError("Tournament not found")
        return t

    def list_tournaments(
        self,
        *,
        status: str | None = None,
        organizer_id: uuid.UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Tournament], int]:
        return self.repo.list(
            status=status,
            organizer_id=organizer_id,
            search=search,
            limit=limit,
            offset=offset,
        )

    def create(self, organizer_id: uuid.UUID, data: dict) -> Tournament:
        slug = data.pop("slug", None) or _slugify(data["name"])
        base = slug
        i = 1
        while self.repo.get_by_slug(slug) is not None:
            i += 1
            slug = f"{base}-{i}"
        tournament = Tournament(
            organizer_id=organizer_id, slug=slug, status=TournamentStatus.DRAFT, **data
        )
        self.repo.add(tournament)
        self.repo.commit()
        self.repo.refresh(tournament)
        return tournament

    def _assert_can_manage(
        self, tournament: Tournament, user_id: uuid.UUID, role: UserRole
    ) -> None:
        if role == UserRole.ADMIN or tournament.organizer_id == user_id:
            return
        raise PermissionDeniedError("Only the organizer or an admin can manage this tournament")

    # -- entries -------------------------------------------------------------
    def register(self, tournament_id: uuid.UUID, user_id: uuid.UUID) -> TournamentEntry:
        tournament = self.get(tournament_id)
        if tournament.status not in (TournamentStatus.DRAFT, TournamentStatus.OPEN):
            raise ConflictError("Registration is closed for this tournament")
        existing = self.repo.get_entry_for_user(tournament_id, user_id)
        if existing is not None:
            raise ConflictError("You are already registered for this tournament")
        entries = self.repo.list_entries(tournament_id)
        if len(entries) >= tournament.max_entries:
            raise ConflictError("Tournament is full")
        entry = TournamentEntry(
            tournament_id=tournament_id,
            user_id=user_id,
            seed=len(entries) + 1,
            eliminated=False,
        )
        self.repo.add_entry(entry)
        self.repo.commit()
        self.repo.refresh(entry)
        return entry

    def unregister(self, tournament_id: uuid.UUID, user_id: uuid.UUID) -> None:
        tournament = self.get(tournament_id)
        if tournament.status == TournamentStatus.IN_PROGRESS:
            raise ConflictError("Cannot unregister once the tournament is in progress")
        entry = self.repo.get_entry_for_user(tournament_id, user_id)
        if entry is None:
            raise NotFoundError("You are not registered for this tournament")
        self.repo.delete_entry(entry)
        self.repo.commit()

    def list_entries(self, tournament_id: uuid.UUID) -> list[TournamentEntry]:
        self.get(tournament_id)
        return self.repo.list_entries(tournament_id)

    # -- bracket -------------------------------------------------------------
    def generate_bracket(
        self, tournament_id: uuid.UUID, user_id: uuid.UUID, role: UserRole
    ) -> list[TournamentMatch]:
        tournament = self.get(tournament_id)
        self._assert_can_manage(tournament, user_id, role)
        if tournament.format != TournamentFormat.SINGLE_ELIMINATION:
            raise ConflictError("Only single-elimination brackets are supported")
        entries = self.repo.list_entries(tournament_id)
        if len(entries) < 2:
            raise ConflictError("At least 2 registered entries are required")

        self.repo.delete_matches(tournament_id)
        size = 1 << (len(entries) - 1).bit_length()  # next power of two
        rounds = int(math.log2(size))
        order = _bracket_seed_order(size)
        by_seed = {e.seed: e for e in entries}

        for slot in range(size // 2):
            home = by_seed.get(order[slot * 2])
            away = by_seed.get(order[slot * 2 + 1])
            self.repo.add_match(
                TournamentMatch(
                    tournament_id=tournament_id,
                    round_number=1,
                    slot=slot,
                    home_entry_id=home.id if home else None,
                    away_entry_id=away.id if away else None,
                )
            )

        for rnd in range(2, rounds + 1):
            count = size // (2**rnd)
            for slot in range(count):
                self.repo.add_match(
                    TournamentMatch(tournament_id=tournament_id, round_number=rnd, slot=slot)
                )

        tournament.status = TournamentStatus.IN_PROGRESS
        tournament.starts_at = tournament.starts_at or datetime.now(UTC)
        self.repo.commit()

        self._resolve_byes(tournament_id)
        return self.repo.list_matches(tournament_id)

    def _matches_by_round(self, tournament_id: uuid.UUID) -> dict[int, list[TournamentMatch]]:
        rounds: dict[int, list[TournamentMatch]] = {}
        for m in self.repo.list_matches(tournament_id):
            rounds.setdefault(m.round_number, []).append(m)
        return rounds

    def _get_bracket_match(
        self, tournament_id: uuid.UUID, rnd: int, slot: int
    ) -> TournamentMatch | None:
        return self.db.query(TournamentMatch).filter_by(
            tournament_id=tournament_id, round_number=rnd, slot=slot
        ).one_or_none()

    def _advance(self, tournament_id: uuid.UUID, match: TournamentMatch) -> None:
        nxt = self._get_bracket_match(tournament_id, match.round_number + 1, match.slot // 2)
        if nxt is None:
            return
        if match.slot % 2 == 0:
            nxt.home_entry_id = match.winner_entry_id
        else:
            nxt.away_entry_id = match.winner_entry_id

    def _resolve_byes(self, tournament_id: uuid.UUID) -> None:
        """Push lone competitors forward until they meet a real opponent."""
        rounds = self._matches_by_round(tournament_id)
        if not rounds:
            return
        max_round = max(rounds)
        changed = True
        while changed:
            changed = False
            rounds = self._matches_by_round(tournament_id)
            for rnd in range(1, max_round + 1):
                for m in rounds.get(rnd, []):
                    if m.winner_entry_id is not None:
                        continue
                    home, away = m.home_entry_id, m.away_entry_id
                    if home and not away:
                        m.winner_entry_id = home
                    elif away and not home:
                        m.winner_entry_id = away
                    else:
                        continue
                    changed = True
                    if rnd < max_round:
                        self._advance(tournament_id, m)
        self.repo.commit()

    def record_result(
        self,
        tournament_id: uuid.UUID,
        user_id: uuid.UUID,
        role: UserRole,
        *,
        bracket_match_id: uuid.UUID,
        winner_entry_id: uuid.UUID,
        home_score: int = 0,
        away_score: int = 0,
    ) -> TournamentMatch:
        tournament = self.get(tournament_id)
        self._assert_can_manage(tournament, user_id, role)
        match = self.db.get(TournamentMatch, bracket_match_id)
        if match is None or match.tournament_id != tournament_id:
            raise NotFoundError("Bracket fixture not found")
        if match.winner_entry_id is not None:
            raise ConflictError("This fixture already has a recorded winner")
        if winner_entry_id not in (match.home_entry_id, match.away_entry_id):
            raise ConflictError("Winner must be one of the two competitors in this fixture")
        if match.home_entry_id is None or match.away_entry_id is None:
            raise ConflictError("Cannot record a result for a fixture with a bye")

        match.winner_entry_id = winner_entry_id
        loser_id = (
            match.away_entry_id
            if winner_entry_id == match.home_entry_id
            else match.home_entry_id
        )
        loser = self.repo.get_entry(loser_id)
        if loser is not None:
            loser.eliminated = True

        rounds = self._matches_by_round(tournament_id)
        max_round = max(rounds)
        if match.round_number < max_round:
            self._advance(tournament_id, match)
        else:
            winner = self.repo.get_entry(winner_entry_id)
            if winner is not None:
                winner.final_placement = 1
            if loser is not None:
                loser.final_placement = 2
            tournament.status = TournamentStatus.COMPLETED
            tournament.ends_at = datetime.now(UTC)

        self.repo.commit()
        self.repo.refresh(match)
        return match

    # -- standings -----------------------------------------------------------
    def standings(self, tournament_id: uuid.UUID) -> list[dict]:
        self.get(tournament_id)
        entries = self.repo.list_entries(tournament_id)

        def sort_key(e: TournamentEntry) -> tuple:
            placement = e.final_placement if e.final_placement is not None else 999
            alive = 0 if not e.eliminated else 1
            return (placement, alive, e.seed or 999)

        ordered = sorted(entries, key=sort_key)
        rows: list[dict] = []
        for rank, e in enumerate(ordered, start=1):
            rows.append(
                {
                    "rank": rank,
                    "entry_id": e.id,
                    "user_id": e.user_id,
                    "seed": e.seed,
                    "eliminated": e.eliminated,
                    "final_placement": e.final_placement,
                }
            )
        return rows

    def bracket_view(self, tournament_id: uuid.UUID) -> dict:
        tournament = self.get(tournament_id)
        matches = self.repo.list_matches(tournament_id)
        rounds = max((m.round_number for m in matches), default=0)
        out = []
        for m in matches:
            home = self.repo.get_entry(m.home_entry_id) if m.home_entry_id else None
            away = self.repo.get_entry(m.away_entry_id) if m.away_entry_id else None
            winner = self.repo.get_entry(m.winner_entry_id) if m.winner_entry_id else None
            out.append(
                {
                    "id": m.id,
                    "round_number": m.round_number,
                    "slot": m.slot,
                    "home_entry_id": m.home_entry_id,
                    "away_entry_id": m.away_entry_id,
                    "home_user_id": home.user_id if home else None,
                    "away_user_id": away.user_id if away else None,
                    "winner_entry_id": winner.id if winner else None,
                    "match_id": m.match_id,
                    "status": "completed" if m.winner_entry_id else "pending",
                }
            )
        return {
            "tournament_id": tournament_id,
            "format": tournament.format,
            "rounds": rounds,
            "matches": out,
        }
