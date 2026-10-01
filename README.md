# RALLY

> **Find your people. Do more together.**

RALLY is a social activity marketplace and community platform. People discover
activities and venues, find others to play with, create and join activities,
book venues, split costs, pay, chat, check in, record and verify results, gain
activity-specific MMR, climb leaderboards, run tournaments, build reputation
and earn achievements.

RALLY begins with social sports and expands into **games, outdoor, social and
creative** activities through a config-driven activity engine.

> **Independence notice.** RALLY is an original product. It does not copy the
> code, assets, branding, proprietary UI or data of any other platform
> (including Reclub). Any resemblance to category conventions is generic and
> intentional only at the level of common product patterns.

---

## Core loop

```
DISCOVER -> FIND PEOPLE -> JOIN -> BOOK -> PAY -> CHAT -> CHECK IN
        -> PARTICIPATE -> RECORD RESULT -> VERIFY -> UPDATE MMR
        -> LEADERBOARD -> REPUTATION -> DISCOVER MORE
```

## Activity categories

`sports` · `games` · `outdoor` · `social` · `creative`

Behaviour for each category/type is **config-driven** (see
`docs/ARCHITECTURE.md` and the `activity_categories`, `activity_types`,
`activity_configs` tables in `docs/DATABASE.md`). No per-activity logic is
hardcoded into random components.

## Roles (RBAC, enforced server-side)

`user` · `host` · `club_organizer` · `venue_manager` · `tournament_organizer`
· `moderator` · `admin`

RBAC is enforced in the backend. The frontend may hide UI, but it is **never**
the security boundary.

## Stack

| Layer     | Technology |
|-----------|------------|
| Backend   | FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis, python-jose/passlib, WebSockets |
| Frontend  | React 18 + TypeScript + Vite, React Router, TanStack Query, Zustand, React Hook Form + Zod, Tailwind CSS, PWA (vite-plugin-pwa) |
| Infra     | Docker Compose (frontend, backend, postgres, redis) |
| Tests     | pytest + httpx (backend); Vitest + Testing Library (frontend) |

## Repository layout

```
rally/
├─ apps/
│  ├─ api/        # FastAPI backend (router -> service -> repository -> model)
│  └─ web/        # React 18 + TS + Vite PWA
├─ packages/
│  └─ shared/     # Shared types/contracts between api and web
├─ infra/         # Docker Compose, provisioning, ops
├─ docs/          # Product, architecture, database, design, page map
├─ README.md
├─ AGENTS.md      # Engineering conventions (read before contributing)
├─ PROJECT.md     # Roadmap checklist
└─ STATUS.md      # Current state of the build
```

## Branding

Brand is a single swappable source of truth:
- Frontend: `apps/web/src/config/brand.ts`
- Backend:  `apps/api/app/core/brand.py`

Both read environment variables (`BRAND_NAME`, `BRAND_TAGLINE`, …) with
defaults `BRAND_NAME=RALLY` and tagline `Find your people. Do more together.`
Rebrand without touching product code.

## Getting started (planned — see STATUS.md for what is live)

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

## Conventions

- Layered backend: **router -> service -> repository -> model**, Pydantic
  schemas at the boundary. No business logic in route handlers.
- MMR is activity-specific Elo-style, transactional, immutable history, and is
  **never** accepted from the client.
- Payment, map and email are provider abstractions with clearly-labelled
  dev/mock providers. Production providers are configured via env. We never
  pretend an external service is connected.
- Every critical flow is idempotent; `audit_logs` record admin, MMR, booking,
  payment and moderation actions.
- Real, working, tested code only. Seed data is labelled **DEMO DATA**.

See `AGENTS.md` for the full engineering contract.
