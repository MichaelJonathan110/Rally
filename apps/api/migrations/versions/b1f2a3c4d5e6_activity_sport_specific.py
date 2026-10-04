"""activity sport-specific fields

Adds the sports-only activity columns (sport_slug + derived sport_category,
variant/format/metrics) plus the venue_court_id resource link and the legacy
activity_type column. All are nullable, so rows created before the sports pivot
stay valid.

Revision ID: b1f2a3c4d5e6
Revises: 83302ff4ea29
Create Date: 2026-10-02 15:20:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1f2a3c4d5e6"
down_revision: str | None = "83302ff4ea29"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SPORT_CATEGORY = sa.Enum(
    "racket",
    "team",
    "combat",
    "strength",
    "running",
    "cycling",
    "water",
    "winter",
    "precision",
    "gymnastics",
    "outdoor",
    "other",
    name="sportcategory",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        _SPORT_CATEGORY.create(bind, checkfirst=True)
    op.add_column("activities", sa.Column("sport_slug", sa.String(length=40), nullable=True))
    op.add_column("activities", sa.Column("sport_category", _SPORT_CATEGORY, nullable=True))
    op.add_column("activities", sa.Column("sport_variant", sa.String(length=40), nullable=True))
    op.add_column("activities", sa.Column("sport_format", sa.String(length=40), nullable=True))
    op.add_column("activities", sa.Column("sport_metrics", sa.JSON(), nullable=True))
    op.add_column("activities", sa.Column("activity_type", sa.String(length=40), nullable=True))
    op.add_column("activities", sa.Column("venue_court_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_activities_sport_slug"), "activities", ["sport_slug"], unique=False)
    op.create_index(
        op.f("ix_activities_sport_category"), "activities", ["sport_category"], unique=False
    )
    op.create_index(
        op.f("ix_activities_activity_type"), "activities", ["activity_type"], unique=False
    )
    op.create_index(
        op.f("ix_activities_venue_court_id"), "activities", ["venue_court_id"], unique=False
    )
    op.create_foreign_key(
        "fk_activities_venue_court_id",
        "activities",
        "venue_courts",
        ["venue_court_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_activities_venue_court_id", "activities", type_="foreignkey")
    op.drop_index(op.f("ix_activities_venue_court_id"), table_name="activities")
    op.drop_index(op.f("ix_activities_activity_type"), table_name="activities")
    op.drop_index(op.f("ix_activities_sport_category"), table_name="activities")
    op.drop_index(op.f("ix_activities_sport_slug"), table_name="activities")
    op.drop_column("activities", "venue_court_id")
    op.drop_column("activities", "activity_type")
    op.drop_column("activities", "sport_metrics")
    op.drop_column("activities", "sport_format")
    op.drop_column("activities", "sport_variant")
    op.drop_column("activities", "sport_category")
    op.drop_column("activities", "sport_slug")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        _SPORT_CATEGORY.drop(bind, checkfirst=True)
