"""Boot the RALLY API on a local SQLite database (dev / e2e only).

PostgreSQL-specific column types are compiled to SQLite-compatible ones and the
schema is created from the SQLAlchemy models, so the server runs with zero
external services. Usage::

    .venv/Scripts/python scripts/serve_sqlite.py [--port 8001] [--db rally_dev.db]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))



def _zero_literal(type_) -> str:  # noqa: ANN001
    """Type-appropriate literal used when a NOT NULL column is added to a
    populated table (SQLite requires a default in that case)."""
    from sqlalchemy import Boolean, DateTime, Float, Integer, Numeric

    if isinstance(type_, Boolean):
        return "0"
    if isinstance(type_, (Integer, Numeric, Float)):
        return "0"
    if isinstance(type_, DateTime):
        # SQLite forbids CURRENT_TIMESTAMP (and any parenthesised expression)
        # as the default of a column added via ALTER TABLE ... ADD COLUMN, so a
        # constant ISO literal is used instead.
        return "'1970-01-01 00:00:00'"
    return "''"


def _constant_default(column) -> str | None:  # noqa: ANN001
    """SQL literal for a *constant* ``server_default``, else ``None``.

    ``ALTER TABLE ... ADD COLUMN`` in SQLite only accepts constant defaults, so
    SQL-function defaults such as ``now()`` / ``gen_random_uuid()`` (used for
    Postgres server defaults) cannot be replayed and return ``None``; callers
    then fall back to a type-appropriate constant.
    """
    from sqlalchemy.sql.elements import TextClause

    server_default = column.server_default
    if server_default is None:
        return None
    arg = server_default.arg
    if isinstance(arg, bool):
        return "1" if arg else "0"
    if isinstance(arg, (int, float)):
        return str(arg)
    if isinstance(arg, TextClause):
        return arg.text
    if isinstance(arg, str):
        return "'" + arg.replace("'", "''") + "'"
    return None


def _add_column_ddl(column, dialect) -> str:  # noqa: ANN001
    parts = [f'"{column.name}" {column.type.compile(dialect=dialect)}']
    default = _constant_default(column)
    if default is None and not column.nullable:
        default = _zero_literal(column.type)
    if default is not None:
        parts.append(f"DEFAULT {default}")
    if not column.nullable:
        parts.append("NOT NULL")
    return " ".join(parts)


def reconcile_schema(engine) -> list[str]:  # noqa: ANN001
    """Add model columns missing from existing tables.

    ``Base.metadata.create_all`` only creates missing *tables*; it never alters
    an existing one. A dev database created by an older model revision therefore
    drifts (e.g. ``users`` lacking ``email_verified``). This brings it back in
    line so the API boots against a stale file without manual ALTERs.
    """
    from app.models import Base  # local import: avoids import at module load

    added: list[str] = []
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                ddl = _add_column_ddl(column, engine.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))
                added.append(f"{table.name}.{column.name}")
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--db", default="rally_dev.db")
    parser.add_argument("--fresh", action="store_true", help="drop and recreate the file")
    args = parser.parse_args()

    db_path = (ROOT / args.db).resolve()
    if args.fresh and db_path.exists():
        db_path.unlink()

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"

    from sqlalchemy import create_engine
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy.ext.compiler import compiles

    @compiles(PG_UUID, "sqlite")
    def _compile_uuid_sqlite(type_, compiler, **kw):  # noqa: ANN001
        return "CHAR(32)"

    from app.models import Base  # noqa: E402

    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    Base.metadata.create_all(engine)
    added = reconcile_schema(engine)
    if added:
        print(f"reconciled schema: added {added}", file=sys.stderr)

    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
