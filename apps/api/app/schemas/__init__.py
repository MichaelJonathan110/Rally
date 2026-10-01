"""Pydantic v2 schemas package (API boundary).

Schemas are split into Create / Update / Read variants. ORM objects are never
exposed directly over the API. Concrete domain schemas are added in later
batches as their services land.
"""
from __future__ import annotations

from app.schemas.common import ORMModel, Page

__all__ = ["ORMModel", "Page"]
