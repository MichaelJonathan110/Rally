"""Regression tests for the dev-SQLite schema self-heal helper.

``scripts/serve_sqlite.py`` boots the API against a local SQLite file and calls
``reconcile_schema`` to add model columns missing from an existing table (a dev
DB created by an older model revision otherwise drifts, e.g. ``users`` lacking
``email_verified`` — which made ``POST /auth/register`` return 500).
"""
from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "serve_sqlite", ROOT / "scripts" / "serve_sqlite.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def stale_db(tmp_path):
    """A ``users`` table with only two columns (missing every model column)."""
    db = tmp_path / "stale.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE users (id CHAR(32) PRIMARY KEY, email VARCHAR(255) NOT NULL)"
    )
    conn.execute("INSERT INTO users (id, email) VALUES ('a', 'a@example.com')")
    conn.commit()
    conn.close()
    return db


def test_reconcile_adds_missing_columns_without_crashing(stale_db):
    module = _load_module()
    engine = create_engine(f"sqlite:///{stale_db.as_posix()}")
    added = module.reconcile_schema(engine)

    names = {c["name"] for c in inspect(engine).get_columns("users")}
    # The column whose absence caused the register 500 must be healed.
    assert "email_verified" in names
    # NOT NULL DateTime columns (created_at/updated_at) must be addable too —
    # SQLite rejects CURRENT_TIMESTAMP as an ALTER TABLE default.
    assert "created_at" in names and "updated_at" in names
    assert any(a.endswith("email_verified") for a in added)


def test_reconcile_preserves_existing_rows(stale_db):
    module = _load_module()
    engine = create_engine(f"sqlite:///{stale_db.as_posix()}")
    module.reconcile_schema(engine)

    with engine.connect() as conn:
        rows = conn.exec_driver_sql("SELECT id, email FROM users").fetchall()
    assert rows == [("a", "a@example.com")]


def test_reconcile_is_idempotent(stale_db):
    module = _load_module()
    engine = create_engine(f"sqlite:///{stale_db.as_posix()}")
    module.reconcile_schema(engine)
    # A second pass must add nothing and must not raise.
    assert module.reconcile_schema(engine) == []
