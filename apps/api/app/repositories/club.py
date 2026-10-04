"""Club data access."""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.club import Club, ClubMember
from app.repositories.base import BaseRepository


class ClubRepository(BaseRepository[Club]):
    model = Club

    def get(self, entity_id: uuid.UUID) -> Club | None:
        return self.db.get(Club, entity_id)

    def get_by_slug(self, slug: str) -> Club | None:
        return self.db.scalar(select(Club).where(Club.slug == slug))

    def list(
        self,
        *,
        category: str | None = None,
        city: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Club], int]:
        stmt = select(Club)
        if category is not None:
            stmt = stmt.where(Club.category == category)
        if city is not None:
            stmt = stmt.where(Club.city == city)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(Club.name.ilike(like))
        total = int(
            self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        )
        rows = self.db.scalars(
            stmt.order_by(Club.name.asc()).limit(limit).offset(offset)
        ).all()
        return rows, total

    def member_count(self, club_id: uuid.UUID) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(ClubMember)
                .where(ClubMember.club_id == club_id, ClubMember.is_active.is_(True))
            )
            or 0
        )

    def get_member(self, club_id: uuid.UUID, user_id: uuid.UUID) -> ClubMember | None:
        return self.db.scalar(
            select(ClubMember).where(
                ClubMember.club_id == club_id, ClubMember.user_id == user_id
            )
        )

    def list_members(self, club_id: uuid.UUID) -> Sequence[ClubMember]:
        return self.db.scalars(
            select(ClubMember)
            .where(ClubMember.club_id == club_id)
            .order_by(ClubMember.joined_at.asc().nulls_last())
        ).all()

    def add_member(self, member: ClubMember) -> ClubMember:
        self.db.add(member)
        self.db.flush()
        return member

    def remove_member(self, member: ClubMember) -> None:
        self.db.delete(member)
        self.db.flush()
