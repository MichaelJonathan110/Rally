"""MMR is sport-specific: add sport_slug to ratings + leaderboards

A player now has one rating per **sport slug** rather than one per activity
category. This migration:

* adds ``mmr_ratings.sport_slug`` and backfills legacy rows with a
  ``category:<cat>`` scope key (kept distinct from any real sport slug);
* swaps the ``(user_id, category)`` unique constraint for ``(user_id, sport_slug)``;
* adds ``leaderboard_entries.sport_slug`` and swaps its uniqueness to
  ``(sport_slug, period, user_id)``;
* replaces the single-column ``mmr_history.match_result_id`` unique constraint
  with the composite ``(match_result_id, user_id)`` idempotency key so team
  results (one history row per member) can be stored.

All columns are added nullable-with-backfill then set NOT NULL, so existing rows
stay valid. ``downgrade`` reverses each step.

Revision ID: c2d3e4f5a6b7
Revises: b1f2a3c4d5e6
Create Date: 2026-10-02 16:40:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1f2a3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEGACY_PREFIX = "category:"


def upgrade() -> None:
    # -- mmr_ratings ---------------------------------------------------------
    op.add_column(
        "mmr_ratings", sa.Column("sport_slug", sa.String(length=60), nullable=True)
    )
    # Backfill: legacy rows scope by category, kept distinct from real slugs.
    op.execute(
        "UPDATE mmr_ratings "
        f"SET sport_slug = '{_LEGACY_PREFIX}' || category "
        "WHERE sport_slug IS NULL"
    )
    op.alter_column("mmr_ratings", "sport_slug", nullable=False)
    op.create_index(
        op.f("ix_mmr_ratings_sport_slug"), "mmr_ratings", ["sport_slug"], unique=False
    )
    op.drop_constraint(
        "uq_mmr_ratings_user_category", "mmr_ratings", type_="unique"
    )
    op.create_unique_constraint(
        "uq_mmr_ratings_user_sport", "mmr_ratings", ["user_id", "sport_slug"]
    )

    # -- leaderboard_entries -------------------------------------------------
    op.add_column(
        "leaderboard_entries",
        sa.Column("sport_slug", sa.String(length=60), nullable=True),
    )
    op.execute(
        "UPDATE leaderboard_entries "
        f"SET sport_slug = '{_LEGACY_PREFIX}' || category "
        "WHERE sport_slug IS NULL"
    )
    op.alter_column("leaderboard_entries", "sport_slug", nullable=False)
    op.create_index(
        op.f("ix_leaderboard_entries_sport_slug"),
        "leaderboard_entries",
        ["sport_slug"],
        unique=False,
    )
    op.drop_constraint(
        "uq_leaderboard_entries_cat_period_user", "leaderboard_entries", type_="unique"
    )
    op.create_unique_constraint(
        "uq_leaderboard_entries_sport_period_user",
        "leaderboard_entries",
        ["sport_slug", "period", "user_id"],
    )

    # -- mmr_history ---------------------------------------------------------
    op.drop_constraint("uq_mmr_history_match_result", "mmr_history", type_="unique")
    op.create_unique_constraint(
        "uq_mmr_history_result_user", "mmr_history", ["match_result_id", "user_id"]
    )


def downgrade() -> None:
    # -- mmr_history ---------------------------------------------------------
    op.drop_constraint("uq_mmr_history_result_user", "mmr_history", type_="unique")
    op.create_unique_constraint(
        "uq_mmr_history_match_result", "mmr_history", ["match_result_id"]
    )

    # -- leaderboard_entries -------------------------------------------------
    op.drop_constraint(
        "uq_leaderboard_entries_sport_period_user", "leaderboard_entries", type_="unique"
    )
    op.create_unique_constraint(
        "uq_leaderboard_entries_cat_period_user",
        "leaderboard_entries",
        ["category", "period", "user_id"],
    )
    op.drop_index(
        op.f("ix_leaderboard_entries_sport_slug"), table_name="leaderboard_entries"
    )
    op.drop_column("leaderboard_entries", "sport_slug")

    # -- mmr_ratings ---------------------------------------------------------
    op.drop_constraint("uq_mmr_ratings_user_sport", "mmr_ratings", type_="unique")
    op.create_unique_constraint(
        "uq_mmr_ratings_user_category", "mmr_ratings", ["user_id", "category"]
    )
    op.drop_index(op.f("ix_mmr_ratings_sport_slug"), table_name="mmr_ratings")
    op.drop_column("mmr_ratings", "sport_slug")
