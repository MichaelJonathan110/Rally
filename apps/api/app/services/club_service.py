"""Club business logic: create clubs, join/leave, membership listing."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.core.sport_fields import is_known_sport, resolve_club_sport
from app.models.club import Club, ClubMember
from app.models.enums import UserRole
from app.repositories.club import ClubRepository

#: Upper bound used when filtering clubs by sport in the service layer.
_SPORT_FILTER_SCAN_LIMIT = 1000


class ClubService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ClubRepository(db)

    def get(self, club_id: uuid.UUID) -> Club:
        club = self.repo.get(club_id)
        if club is None:
            raise NotFoundError("Club not found")
        return club

    def list_clubs(
        self,
        *,
        category: str | None = None,
        city: str | None = None,
        search: str | None = None,
        sport_slug: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Club], int]:
        if sport_slug is not None:
            # Sport binding is newer than the repository query API, so the
            # sport filter is applied here (after the other predicates) to keep
            # the repo diff-free and the total accurate for the filtered set.
            rows, _ = self.repo.list(
                category=category,
                city=city,
                search=search,
                limit=_SPORT_FILTER_SCAN_LIMIT,
                offset=0,
            )
            filtered = [c for c in rows if c.sport_slug == sport_slug]
            return list(filtered[offset : offset + limit]), len(filtered)
        rows, total = self.repo.list(
            category=category, city=city, search=search, limit=limit, offset=offset
        )
        return list(rows), total

    def member_count(self, club_id: uuid.UUID) -> int:
        return self.repo.member_count(club_id)

    def _apply_sport(self, data: dict) -> dict:
        """Validate ``sport_slug`` against the catalog and derive categories.

        Rejects unknown slugs with :class:`ValidationError` (HTTP 400); RALLY is
        sports-only, so a club must name a real catalog sport.
        """
        data = dict(data)
        sport_slug = data.get("sport_slug")
        if sport_slug is not None:
            if not is_known_sport(str(sport_slug)):
                raise ValidationError(f"Unknown sport slug {sport_slug!r}")
            resolved = resolve_club_sport(str(sport_slug))
            data["sport_slug"] = resolved["sport_slug"]
            data["sport_category"] = resolved["sport_category"]
            data.setdefault("category", resolved["category"])
        return data

    def create(self, owner_id: uuid.UUID, data: dict) -> Club:
        data = self._apply_sport(data)
        slug = data.get("slug")
        if slug and self.repo.get_by_slug(slug) is not None:
            raise ConflictError("A club with that slug already exists")
        club = Club(owner_id=owner_id, **data)
        self.repo.add(club)
        self.repo.add_member(
            ClubMember(
                club_id=club.id,
                user_id=owner_id,
                role=UserRole.CLUB_ORGANIZER,
                is_active=True,
                joined_at=datetime.now(UTC),
            )
        )
        self.repo.commit()
        self.repo.refresh(club)
        return club

    def update(self, club_id: uuid.UUID, actor_id: uuid.UUID, data: dict) -> Club:
        club = self.get(club_id)
        if club.owner_id != actor_id:
            raise PermissionDeniedError("Only the club owner can update this club")
        changes = {k: v for k, v in data.items() if v is not None}
        changes = self._apply_sport(changes)
        for key, value in changes.items():
            setattr(club, key, value)
        self.repo.commit()
        self.repo.refresh(club)
        return club

    def join(self, club_id: uuid.UUID, user_id: uuid.UUID) -> ClubMember:
        club = self.get(club_id)
        existing = self.repo.get_member(club_id, user_id)
        if existing is not None and existing.is_active:
            raise ConflictError("You are already a member of this club")
        if not club.is_public:
            raise PermissionDeniedError("This club is private (invite only)")
        if existing is not None:  # re-activate a previously-left membership
            existing.is_active = True
            existing.joined_at = datetime.now(UTC)
            member = existing
        else:
            member = ClubMember(
                club_id=club_id,
                user_id=user_id,
                role=UserRole.USER,
                is_active=True,
                joined_at=datetime.now(UTC),
            )
            self.repo.add_member(member)
        self.repo.commit()
        self.repo.refresh(member)
        return member

    def leave(self, club_id: uuid.UUID, user_id: uuid.UUID) -> None:
        club = self.get(club_id)
        if club.owner_id == user_id:
            raise PermissionDeniedError("The club owner cannot leave their own club")
        member = self.repo.get_member(club_id, user_id)
        if member is None or not member.is_active:
            raise NotFoundError("You are not a member of this club")
        self.repo.remove_member(member)
        self.repo.commit()

    def list_members(self, club_id: uuid.UUID) -> list[ClubMember]:
        self.get(club_id)  # 404 if missing
        return list(self.repo.list_members(club_id))
