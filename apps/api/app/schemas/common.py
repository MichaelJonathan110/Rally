"""Shared schema primitives."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for read schemas that are populated from ORM objects."""

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_datetimes_utc(self, value: Any) -> Any:
        """Emit datetimes as explicit UTC ISO-8601 (``...Z``).

        RALLY stores timestamps in UTC but SQLite hands them back *naive*, so a
        naive value would be serialised without an offset and every browser
        (e.g. Asia/Jakarta, UTC+7) would re-interpret it as its own local time -
        turning an upcoming 09:00Z activity into a "7 jam lalu" past one. Making
        the UTC offset explicit lets clients convert to local time correctly.
        """
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=UTC)
            return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        return value


class Pagination(BaseModel):
    """Query parameters describing a slice of a collection."""

    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class Page(BaseModel, Generic[T]):
    """Generic pagination envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int
