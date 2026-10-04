# STATUS.md — RALLY Build Status

_Last updated: maintenance fire 2026-10-04 (schema-drift self-heal fix + hygiene)._

## What exists right now

RALLY is a working full-stack app: FastAPI backend (`apps/api`) + Vite/React/TS
PWA (`apps/web`), running locally against SQLite for dev/e2e. Backend layering
(router -> service -> repository -> model), server-enforced RBAC, config-driven
activity engine, immutable MMR history and idempotent critical flows follow
`AGENTS.md`. All figures below were produced by commands run this fire.

### Verified this fire (raw output captured in the batch report)
- **pytest: 264 passed, 1 warning** (`.venv/Scripts/python -m pytest -o addopts="" -q`).
- **tsc --noEmit: PASS (exit 0)**; **vite build: PASS** (2106 modules, PWA
  precache 76 entries / 693.97 KiB, `dist/sw.js`).
- **Live API** on `127.0.0.1:8001`: `health=200`; **register=201**,
  **login=200**; activities=419, venues=619, clubs=3.
- **Web** on `127.0.0.1:4173`: `=200`; browser (puppeteer) pass over `/`,
  `/discover`, `/login`, `/venues`, `/leaderboard` -> BAD_TEXT=NONE,
  PAGE_ERRORS=NONE, FAILED_REQUESTS=NONE. Register-via-UI ends authed.
- **Fixed:** register returned HTTP 500 — dev SQLite (`rally_dev.db`) had
  drifted (missing `users.email_verified`). `scripts/serve_sqlite.py` now runs
  `reconcile_schema()` after `create_all()` to add model columns missing from an
  existing table, using constant defaults (SQL-function defaults such as
  `gen_random_uuid()`/`now()` are not replayable in SQLite `ADD COLUMN`).
- **Hardened:** the `reconcile_schema` self-heal had a latent bug — it replayed
  SQL-function defaults and used `CURRENT_TIMESTAMP` for NOT NULL `DateTime`
  columns, both of which SQLite's `ALTER TABLE ... ADD COLUMN` rejects
  (`Cannot add a column with non-constant default`), so booting against a
  stale DB could still crash. Now uses constant literals; covered by 3 new
  regression tests (`tests/test_serve_sqlite_reconcile.py`).
- **Restored:** tracked top-level `STATUS.md` (had been deleted by a runaway
  `rm STATUS*.md` hygiene glob; it is not covered by `.gitignore`).

### Surface (counts from the tree)
- API route modules: 23 (`activities, admin, auth, bookings, catalog, chat,
  checkin, clubs, follows, health, matches, matchmaking, media, notifications,
  progress, reports, sports, tournaments, users, venue_map, venues, webhooks`).
- Services: 18; SQLAlchemy models: users/profiles/activities/venues/bookings/
  payments/clubs/chat/MMR/notifications/tournaments/reports ...
- Web pages: 26 (`Home, Discover, CreateActivity, Login, Register, Profile,
  Chat, Leaderboard, Tournaments, Clubs, Venues, VenueMap, Bookings,
  Achievements, Matchmaking, People, Feed, ...`).
- Alembic migrations: 4 (head `d3e4f5a6b7c8` email verification + tokens).
- Backend tests: 23 modules.

## Known gaps (tracked in PROJECT.md)
- No Docker Compose for the full stack; dev runs on SQLite + local processes.
- Frontend unit tests (Vitest) not yet written; `ruff check` has pre-existing
  style debt (mostly `E501`); `mypy` not re-run this fire.
- CI workflow still pending (Phase 0 item).

## Toolchain (recon, verbatim)
- Python 3.11.16 - Node v24.21.0 - npm 11.19.0 - git 2.54.0.windows.1
