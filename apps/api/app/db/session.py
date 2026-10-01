"""Database engine, session factory and FastAPI dependency."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Short connect timeout so health checks degrade to "down" promptly instead of
# hanging when the database is unreachable. `psycopg` accepts connect_timeout.
_connect_args: dict[str, object] = {}
if settings.DATABASE_URL.startswith("postgresql"):
    _connect_args["connect_timeout"] = 3

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Yield a scoped session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
