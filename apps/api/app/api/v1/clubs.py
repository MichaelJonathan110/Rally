"""Club endpoints: list/create, detail, update, join/leave, members."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db
from app.core.sport_fields import is_known_sport
from app.models.enums import ActivityCategory
from app.schemas.club import ClubCreate, ClubMemberRead, ClubRead, ClubUpdate
from app.schemas.common import Page
from app.services.club_service import ClubService

router = APIRouter(prefix="/clubs", tags=["clubs"])

DbSession = Annotated[Session, Depends(get_db)]


def _to_read(service: ClubService, club: object) -> ClubRead:
    data = ClubRead.model_validate(club)
    data.member_count = service.member_count(club.id)  # type: ignore[attr-defined]
    return data


@router.get("", response_model=Page[ClubRead])
def list_clubs(
    db: DbSession,
    category: Annotated[ActivityCategory | None, Query()] = None,
    sport: Annotated[str | None, Query(max_length=40)] = None,
    city: Annotated[str | None, Query(max_length=120)] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[ClubRead]:
    # RALLY is sports-only: an unknown ?sport= slug is a client error (422).
    if sport is not None and not is_known_sport(sport):
        raise HTTPException(
            status_code=422,  # Unprocessable Entity
            detail=f"Unknown sport slug {sport!r}",
        )
    service = ClubService(db)
    rows, total = service.list_clubs(
        category=str(category) if category else None,
        city=city,
        search=search,
        sport_slug=sport,
        limit=limit,
        offset=offset,
    )
    return Page[ClubRead](
        items=[_to_read(service, c) for c in rows], total=total, limit=limit, offset=offset
    )


@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED)
def create_club(payload: ClubCreate, current_user: CurrentUser, db: DbSession) -> ClubRead:
    """Create a club; the caller becomes owner + first member."""
    service = ClubService(db)
    club = service.create(current_user.id, payload.model_dump())
    return _to_read(service, club)


@router.get("/{club_id}", response_model=ClubRead)
def get_club(club_id: uuid.UUID, db: DbSession) -> ClubRead:
    service = ClubService(db)
    return _to_read(service, service.get(club_id))


@router.patch("/{club_id}", response_model=ClubRead)
def update_club(
    club_id: uuid.UUID, payload: ClubUpdate, current_user: CurrentUser, db: DbSession
) -> ClubRead:
    """Update a club (owner only); an unknown sport_slug is rejected (422)."""
    service = ClubService(db)
    club = service.update(club_id, current_user.id, payload.model_dump())
    return _to_read(service, club)


@router.post("/{club_id}/join", response_model=ClubMemberRead)
def join_club(
    club_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> ClubMemberRead:
    member = ClubService(db).join(club_id, current_user.id)
    return ClubMemberRead.model_validate(member)


@router.post("/{club_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_club(club_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    ClubService(db).leave(club_id, current_user.id)


@router.get("/{club_id}/members", response_model=list[ClubMemberRead])
def list_members(club_id: uuid.UUID, db: DbSession) -> list[ClubMemberRead]:
    rows = ClubService(db).list_members(club_id)
    return [ClubMemberRead.model_validate(m) for m in rows]
