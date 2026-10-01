# STATUS.md — RALLY Build Status

_Last updated: BATCH 0 (recon + scaffold + phase 0 docs)._

## What exists right now

This is **Phase 0**: foundations only. No application runtime yet — no API
server, no frontend app, no database, no Docker Compose, no tests. Those begin
in Phase 1 (see `PROJECT.md`). Nothing here pretends to work that does not.

### Verified this batch
- Git repository initialised on branch `main`.
- `.gitignore` covering deps, builds, env, databases, OS files.
- Top-level docs: `README.md`, `AGENTS.md`, `PROJECT.md`, `STATUS.md`.
- `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`,
  `docs/DESIGN_SYSTEM.md`, `docs/PAGE_MAP.md`.
- Brand config single source of truth:
  - `apps/web/src/config/brand.ts` (Vite env, defaults BRAND_NAME=RALLY).
  - `apps/api/app/core/brand.py` — **imports and runs**, emits public brand dict
    (verified with `python -c ...`, raw output captured).
- Monorepo skeleton: `apps/api`, `apps/web`, `packages/shared`, `infra`, `docs`
  (each with `.gitkeep`); Python packages have `__init__.py`.
- `.env.example` present (brand vars).

### Not yet implemented (tracked in PROJECT.md)
- FastAPI app, SQLAlchemy models, Alembic migrations, auth/RBAC, services.
- React app, routing, theming, PWA.
- Docker Compose (postgres, redis, backend, frontend).
- Tests (pytest/httpx, Vitest), lint/type-check config, CI.

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
- `psql` is not installed on PATH. Postgres will be provided via Docker Compose
  in Phase 1; a host client is not required.
- Terminal sessions run bash (Git Bash), not PowerShell; PowerShell cmdlets are
  invoked via `powershell.exe -Command` when needed.

## Next batch
Phase 1 — backend foundation: FastAPI app factory + settings, SQLAlchemy 2.0
base/session, Alembic init, Docker Compose (postgres/redis/backend/frontend),
health endpoints, and the first migrations.
