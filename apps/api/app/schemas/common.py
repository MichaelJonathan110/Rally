"""Shared schema primitives."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ORMModel(BaseModel):
    """Base for read schemas that are populated from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    """Generic pagination envelope."""

    items: list[T]
    total: int
    limit: int
    offset: int
