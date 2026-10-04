"""Generic data-access base for repositories.

Repositories are the only layer allowed to touch the ORM session for reads and
writes; they contain no business rules and no HTTP concerns. SQLAlchemy 2.0
typed style throughout.
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Thin CRUD helper around a single model class."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()

    def commit(self) -> None:
        """Commit the current unit of work (transaction boundary)."""
        self.db.commit()

    def refresh(self, entity: ModelT) -> ModelT:
        self.db.refresh(entity)
        return entity

    def rollback(self) -> None:
        self.db.rollback()

    def count(self) -> int:
        return int(self.db.scalar(select(func.count()).select_from(self.model)) or 0)

    def list(
        self, *, limit: int = 50, offset: int = 0, order_by: Any | None = None
    ) -> Sequence[ModelT]:
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return self.db.scalars(stmt.limit(limit).offset(offset)).all()
