# STATUS.md — RALLY Build Status

_Last updated: BATCH 1 (verify Batch 0 + backend foundation)._

## What exists right now

Phase 1 backend foundation is **real and verified**: a FastAPI service under
`apps/api` with layered structure, SQLAlchemy 2.0 models, an Alembic migration
that round-trips against PostgreSQL, and passing tests. No frontend, no Docker
Compose, no auth yet — those are later batches (see `PROJECT.md`).

### Verified this batch (raw output captured in the batch report)
- FastAPI app factory (`app/main.py`), CORS, lifespan, `/health` +
  `/api/v1/health` returning `{status,version,db}` with a **real DB probe**;
  `/api/v1/brand` exposes the brand payload.
- Settings via `pydantic-settings` (`app/core/config.py`): `DATABASE_URL`,
  `REDIS_URL`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `BRAND_NAME`, CORS.
- `app/db/base.py` (`Base` + UUID PK & timestamp mixins), `app/db/session.py`
  (engine + `SessionLocal` + `get_db`, 3s connect timeout so health degrades
  gracefully).
- SQLAlchemy 2.0 typed models (12 tables): `users`, `profiles`, `activities`,
  `activity_categories`, `activity_participants`, `venues`, `venue_courts`,
  `clubs`, `club_members`, `bookings`, `payments`, `payment_splits`. UUID PKs,
  `created_at`/`updated_at`, FKs with explicit `ondelete`, indexes, unique
  constraints (incl. idempotency keys on bookings/payments).
- Native PG enums store **lowercase values** (via `values_callable`) — verified
  in the live DB.
- Alembic wired to `Base.metadata` (offline + online); initial migration
  `8eae275c9f82` applies, downgrades cleanly (drops enum types too) and
  `alembic check` reports **no drift**.
- `tests/` — 9 tests (health/brand/openapi contracts + model metadata) — pass.
- `ruff check` clean; `mypy` (strict) clean on `app/`.

### Not yet implemented (tracked in PROJECT.md)
- Docker Compose (postgres/redis/backend/frontend).
- Auth (register/login, JWT, refresh), RBAC dependency, audit_logs write path.
- Redis health check, services/repositories, domain schemas beyond common.
- React app, theming, PWA, CI workflow.

## Toolchain (recon, verbatim)
```
Python 3.11.16
v24.21.0            (node)
11.19.0             (npm)
git version 2.54.0.windows.1
Docker version 29.8.0, build 88096ef
Docker Compose version v5.5.1
psql: command not found  (PostgreSQL client not on PATH)
```

## Known blockers / notes
- Terminal sessions run **bash (Git Bash)**, not PowerShell; use `cmd.exe /c`
  for Windows-native tools.
- Host Postgres client not installed; DB verified via a throwaway
  `postgres:16-alpine` Docker container (`-p 55432:5432`). No host client needed.
- Benign warning: `starlette.testclient` emits a StarletteDeprecationWarning
  about `httpx`/`httpx2`; tests pass regardless.

## Next batch
Phase 1 continued — Docker Compose (postgres/redis/backend/frontend), auth
(register/login/JWT), RBAC dependency + role model, `audit_logs`, and the
Redis readiness check.
