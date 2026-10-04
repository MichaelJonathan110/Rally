"""Transactional email: users.email_verified + one_time_tokens table

Adds a boolean ``email_verified`` flag to ``users`` (default false, backfilled
false for existing rows) and a new ``one_time_tokens`` table holding hashed,
single-use, expiring tokens for email verification and password reset.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-10-03 10:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_table(
        "one_time_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_one_time_tokens_token_hash"),
    )
    op.create_index(
        "ix_one_time_tokens_user_id", "one_time_tokens", ["user_id"], unique=False
    )
    op.create_index(
        "ix_one_time_tokens_token_hash", "one_time_tokens", ["token_hash"], unique=False
    )
    op.create_index(
        "ix_one_time_tokens_user_kind", "one_time_tokens", ["user_id", "kind"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_one_time_tokens_user_kind", table_name="one_time_tokens")
    op.drop_index("ix_one_time_tokens_token_hash", table_name="one_time_tokens")
    op.drop_index("ix_one_time_tokens_user_id", table_name="one_time_tokens")
    op.drop_table("one_time_tokens")
    op.drop_column("users", "email_verified")
