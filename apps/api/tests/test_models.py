"""Model metadata contract tests (no database required).

These assert the schema definitions that migrations and services depend on:
every expected table exists, primary keys are UUIDs, timestamps are present and
the idempotency unique constraints are declared.
"""
from __future__ import annotations

from app.db.base import Base
from app.models import (  # noqa: F401  (import registers all tables)
    Activity,
    ActivityCategoryLink,
    ActivityParticipant,
    Booking,
    Club,
    ClubMember,
    Payment,
    PaymentSplit,
    Profile,
    User,
    Venue,
    VenueCourt,
)

EXPECTED_TABLES = {
    # user
    "users",
    "profiles",
    "user_skills",
    "one_time_tokens",
    # social graph
    "follows",
    # activity
    "activities",
    "activity_categories",
    "activity_participants",
    "activity_recurrences",
    # venue
    "venues",
    "venue_courts",
    "venue_availability",
    # club
    "clubs",
    "club_members",
    "club_join_requests",
    # booking
    "bookings",
    "payments",
    "payment_splits",
    "refunds",
    # match
    "matches",
    "match_participants",
    "match_results",
    "result_verifications",
    # rating
    "mmr_ratings",
    "mmr_history",
    "leaderboard_entries",
    # tournament
    "tournaments",
    "tournament_entries",
    "tournament_matches",
    # social + moderation
    "chat_rooms",
    "chat_messages",
    "check_ins",
    "notifications",
    "reviews",
    "achievements",
    "user_achievements",
    "reports",
    "moderation_actions",
}


def test_all_expected_tables_registered() -> None:
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_every_table_has_uuid_primary_key_and_timestamps() -> None:
    for name, table in Base.metadata.tables.items():
        pk_cols = list(table.primary_key.columns)
        assert len(pk_cols) == 1, f"{name} must have a single-column PK"
        assert pk_cols[0].name == "id", f"{name} PK must be named id"
        assert str(pk_cols[0].type) == "UUID", f"{name} PK must be UUID, got {pk_cols[0].type}"
        assert "created_at" in table.columns, f"{name} missing created_at"
        assert "updated_at" in table.columns, f"{name} missing updated_at"


def test_idempotency_unique_constraints_declared() -> None:
    assert Booking.__table__.c.idempotency_key.unique
    assert Payment.__table__.c.idempotency_key.unique


def test_natural_unique_constraints() -> None:
    def uniques(table: object) -> set[str]:
        from sqlalchemy import Table

        assert isinstance(table, Table)
        return {c.name for c in table.constraints if c.__class__.__name__ == "UniqueConstraint"}

    assert "uq_users_email" in uniques(User.__table__)
    assert "uq_users_username" in uniques(User.__table__)
    assert "uq_activity_participants_activity_user" in uniques(ActivityParticipant.__table__)
    assert "uq_club_members_club_user" in uniques(ClubMember.__table__)
    assert "uq_payment_splits_payment_user" in uniques(PaymentSplit.__table__)


def test_foreign_keys_use_cascade_or_set_null() -> None:
    """FKs must declare an explicit ondelete policy (no orphaned rows)."""
    for name, table in Base.metadata.tables.items():
        for fk in table.foreign_keys:
            assert fk.ondelete in {"CASCADE", "SET NULL"}, (
                f"{name}.{fk.parent.name} FK ondelete must be CASCADE or SET NULL"
            )
