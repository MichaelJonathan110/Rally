"""Tournament endpoints: CRUD, registration, bracket, results and standings.

Authorization is enforced server-side. Creating/advancing a tournament requires
the caller to be its organizer or an ADMIN; registration is open to any
authenticated user. The frontend is never the authorization boundary.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.models.enums import TournamentStatus
from app.schemas.common import Page
from app.schemas.tournament import (
    BracketMatchRead,
    BracketRead,
    RecordResultRequest,
    StandingsRead,
    StandingRow,
    TournamentCreate,
    TournamentEntryRead,
    TournamentRead,
    TournamentUpdate,
)
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=Page[TournamentRead])
def list_tournaments(
    db: DbSession,
    status_filter: Annotated[TournamentStatus | None, Query(alias="status")] = None,
    organizer_id: Annotated[uuid.UUID | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=160)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[TournamentRead]:
    rows, total = TournamentService(db).list_tournaments(
        status=str(status_filter) if status_filter else None,
        organizer_id=organizer_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return Page[TournamentRead](
        items=[TournamentRead.model_validate(t) for t in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TournamentRead, status_code=status.HTTP_201_CREATED)
def create_tournament(
    payload: TournamentCreate, current_user: CurrentUser, db: DbSession
) -> TournamentRead:
    """Create a tournament. The caller becomes the organizer."""
    tournament = TournamentService(db).create(current_user.id, payload.model_dump())
    return TournamentRead.model_validate(tournament)


@router.get("/{tournament_id}", response_model=TournamentRead)
def get_tournament(tournament_id: uuid.UUID, db: DbSession) -> TournamentRead:
    return TournamentRead.model_validate(TournamentService(db).get(tournament_id))


@router.patch("/{tournament_id}", response_model=TournamentRead)
def update_tournament(
    tournament_id: uuid.UUID,
    payload: TournamentUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TournamentRead:
    """Organizer/admin only partial update."""
    service = TournamentService(db)
    tournament = service.get(tournament_id)
    service._assert_can_manage(tournament, current_user.id, current_user.role)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tournament, field, value)
    service.repo.commit()
    service.repo.refresh(tournament)
    return TournamentRead.model_validate(tournament)


@router.post(
    "/{tournament_id}/register",
    response_model=TournamentEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    tournament_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> TournamentEntryRead:
    entry = TournamentService(db).register(tournament_id, current_user.id)
    return TournamentEntryRead.model_validate(entry)


@router.delete("/{tournament_id}/register", status_code=status.HTTP_204_NO_CONTENT)
def unregister(tournament_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    TournamentService(db).unregister(tournament_id, current_user.id)


@router.get("/{tournament_id}/entries", response_model=list[TournamentEntryRead])
def list_entries(tournament_id: uuid.UUID, db: DbSession) -> list[TournamentEntryRead]:
    rows = TournamentService(db).list_entries(tournament_id)
    return [TournamentEntryRead.model_validate(e) for e in rows]


@router.post("/{tournament_id}/bracket", response_model=BracketRead)
def generate_bracket(
    tournament_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> BracketRead:
    """Organizer/admin only: build the single-elimination bracket."""
    service = TournamentService(db)
    service.generate_bracket(tournament_id, current_user.id, current_user.role)
    view = service.bracket_view(tournament_id)
    return BracketRead(
        tournament_id=view["tournament_id"],
        format=view["format"],
        rounds=view["rounds"],
        matches=[BracketMatchRead(**m) for m in view["matches"]],
    )


@router.get("/{tournament_id}/bracket", response_model=BracketRead)
def get_bracket(tournament_id: uuid.UUID, db: DbSession) -> BracketRead:
    view = TournamentService(db).bracket_view(tournament_id)
    return BracketRead(
        tournament_id=view["tournament_id"],
        format=view["format"],
        rounds=view["rounds"],
        matches=[BracketMatchRead(**m) for m in view["matches"]],
    )


@router.post("/{tournament_id}/results", response_model=BracketMatchRead)
def record_result(
    tournament_id: uuid.UUID,
    payload: RecordResultRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> BracketMatchRead:
    """Organizer/admin only: record a winner and advance the bracket."""
    service = TournamentService(db)
    match = service.record_result(
        tournament_id,
        current_user.id,
        current_user.role,
        bracket_match_id=payload.bracket_match_id,
        winner_entry_id=payload.winner_entry_id,
        home_score=payload.home_score,
        away_score=payload.away_score,
    )
    view = service.bracket_view(tournament_id)
    for m in view["matches"]:
        if m["id"] == match.id:
            return BracketMatchRead(**m)
    return BracketMatchRead(
        id=match.id,
        round_number=match.round_number,
        slot=match.slot,
        home_entry_id=match.home_entry_id,
        away_entry_id=match.away_entry_id,
        winner_entry_id=match.winner_entry_id,
        match_id=match.match_id,
        status="completed" if match.winner_entry_id else "pending",
    )


@router.get("/{tournament_id}/standings", response_model=StandingsRead)
def standings(tournament_id: uuid.UUID, db: DbSession) -> StandingsRead:
    service = TournamentService(db)
    tournament = service.get(tournament_id)
    rows = service.standings(tournament_id)
    return StandingsRead(
        tournament_id=tournament_id,
        status=tournament.status,
        standings=[StandingRow(**r) for r in rows],
    )
