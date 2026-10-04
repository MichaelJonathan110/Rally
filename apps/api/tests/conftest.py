"""Shared pytest fixtures.

Tests run against a fast in-memory SQLite database so the suite needs no
external services. PostgreSQL-specific UUID columns are compiled to CHAR(32)
for the SQLite dialect; everything else is dialect-neutral.
"""
from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import auth_limiter
from app.db.session import get_db
from app.main import app
from app.models import Base


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Give every test a fresh token bucket so limits don't leak across tests."""
    auth_limiter.reset()


@compiles(PG_UUID, "sqlite")
def _compile_uuid_sqlite(type_: PG_UUID, compiler: object, **kw: object) -> str:
    """Render PostgreSQL UUID as CHAR(32) on SQLite."""
    return "CHAR(32)"


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Fresh in-memory database per test."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient wired to the in-memory database via dependency override."""

    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
