"""Core package: configuration, brand and cross-cutting primitives."""
from __future__ import annotations

from app.core.config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
