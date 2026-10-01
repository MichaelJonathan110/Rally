"""BRAND CONFIG - single swappable source of truth (backend).

Values are read from environment variables with safe defaults so the
service runs with zero configuration. Rebrand by setting BRAND_* env vars.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrandTheme:
    primary: str = "#6366f1"
    accent: str = "#22d3ee"
    radius: str = "0.75rem"


@dataclass(frozen=True)
class Brand:
    name: str = "RALLY"
    tagline: str = "Find your people. Do more together."
    short_name: str = "RALLY"
    domain: str = "rally.example"
    support_email: str = "support@rally.example"
    theme: BrandTheme = field(default_factory=BrandTheme)

    @classmethod
    def from_env(cls) -> "Brand":
        def get(key: str, default: str) -> str:
            v = os.getenv(key)
            return v if v else default

        return cls(
            name=get("BRAND_NAME", "RALLY"),
            tagline=get("BRAND_TAGLINE", "Find your people. Do more together."),
            short_name=get("BRAND_SHORT_NAME", "RALLY"),
            domain=get("BRAND_DOMAIN", "rally.example"),
            support_email=get("BRAND_SUPPORT_EMAIL", "support@rally.example"),
            theme=BrandTheme(
                primary=get("BRAND_PRIMARY", "#6366f1"),
                accent=get("BRAND_ACCENT", "#22d3ee"),
                radius=get("BRAND_RADIUS", "0.75rem"),
            ),
        )

    def to_public_dict(self) -> dict[str, object]:
        """Public, client-safe brand payload (no secrets)."""
        return {
            "name": self.name,
            "tagline": self.tagline,
            "short_name": self.short_name,
            "domain": self.domain,
            "support_email": self.support_email,
            "theme": {
                "primary": self.theme.primary,
                "accent": self.theme.accent,
                "radius": self.theme.radius,
            },
        }


brand = Brand.from_env()
