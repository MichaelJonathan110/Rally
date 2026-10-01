# ARCHITECTURE.md — RALLY System Architecture

## 1. Overview

```
                    ┌──────────────────────────────────────┐
                    │            Browser (PWA)              │
                    │  React 18 + TS + Vite + Tailwind      │
                    │  Router · TanStack Query · Zustand    │
                    │  RHF + Zod · vite-plugin-pwa          │
                    └───────────────┬──────────────────────┘
                                    │ HTTPS / WSS
                    ┌───────────────▼──────────────────────┐
                    │            FastAPI (apps/api)         │
                    │  routers -> services -> repositories  │
                    │  Pydantic v2 schemas at the boundary  │
                    │  RBAC deps · idempotency · audit      │
                    └───┬───────────┬───────────┬──────────┘
                        │           │           │
              ┌─────────▼──┐  ┌─────▼─────┐  ┌──▼───────────────┐
              │ PostgreSQL │  │   Redis   │  │ Provider adapters │
              │ (durable)  │  │ cache/WS  │  │ pay/map/email     │
              └────────────┘  └───────────┘  └───────────────────┘
```

- **PostgreSQL** is the source of truth for all application state.
- **Redis** backs caching, rate limiting, presence and WebSocket fan-out.
- **Provider adapters** (payment, map, email) are interfaces with labelled
  dev/mock implementations and env-configured production implementations.

## 2. Backend layering (mandatory)

```
HTTP  ->  router  ->  service  ->  repository  ->  model (SQLAlchemy)
                         │
                    Pydantic v2 schemas (Create / Update / Read)
```

- **Routers** (`app/api/`): validate input, call one service, serialise output.
  No business logic.
- **Services** (`app/services/`): business rules, transactions, orchestration,
  authorisation checks, idempotency, audit writes.
- **Repositories** (`app/repositories/`): typed data access only.
- **Models** (`app/models/`): SQLAlchemy 2.0 declarative, `Mapped[...]`.
- **Schemas** (`app/schemas/`): Pydantic v2, separate input/output models.

Dependency direction is strictly downward. Routers never import repositories
directly; services never build HTTP responses.

### Module map (planned)
```
apps/api/app/
├─ main.py            # ASGI app factory, middleware, router mounting
├─ core/
│  ├─ brand.py        # brand config (single source of truth)
│  ├─ config.py       # settings (env), 12-factor
│  ├─ security.py     # hashing, JWT, password policy
│  ├─ rbac.py         # roles, permissions, dependencies
│  ├─ idempotency.py  # idempotency keys
│  └─ errors.py       # error types -> HTTP mapping
├─ api/               # routers (activities, venues, payments, chat, mmr, admin...)
├─ services/          # business logic
├─ repositories/      # data access
├─ models/            # SQLAlchemy models
├─ schemas/           # Pydantic schemas
├─ db/                # engine/session, base, alembic env
└─ providers/         # payment/map/email abstractions + dev mocks
```

## 3. Frontend architecture

```
apps/web/src/
├─ config/brand.ts    # brand single source of truth
├─ app/               # app shell, providers (query, theme, auth)
├─ routes/            # route definitions (React Router)
├─ pages/             # route-level screens
├─ components/        # reusable UI (design-system primitives)
├─ features/          # feature slices (activities, booking, chat, mmr...)
├─ lib/               # api client, hooks, utils
├─ stores/            # Zustand client-state stores
└─ styles/            # Tailwind layers, tokens, themes
```

- **Server state:** TanStack Query (cache, retries, invalidation).
- **Client state:** Zustand (UI/ephemeral). Never mirror server state in Zustand.
- **Forms:** React Hook Form + Zod; Zod schemas mirror backend validation.
- **Theming:** CSS variables driven by `brand.ts`; dark + light.
- **PWA:** manifest + service worker via `vite-plugin-pwa`.

## 4. Activity engine (config-driven)

The engine reads configuration rows instead of branching on category in code:

- `activity_categories` — top-level (sports, games, outdoor, social, creative).
- `activity_types` — concrete types within a category.
- `activity_configs` — per-type behaviour: required fields, scoring model
  (`none | sets | score | custom`), `mmr_enabled`, team structure, min/max
  players, capacity rules, verification policy.

Adding a new activity type is a **data** change. No per-activity `if` branches
in random components; the frontend renders dynamic fields from the config.

## 5. MMR engine

- Activity-specific Elo-style rating, per `activity_type`.
- Computed **server-side** from verified results. **Never** accepted from the
  client.
- Transactional update inside a single DB transaction with the verification.
- **Immutable** `mmr_history` (append-only). Corrections are new rows.
- **Idempotent per verified match**: a unique constraint on
  `(match_id, activity_type_id)` (or an idempotency key) guarantees a verified
  result updates MMR exactly once.
- Leaderboards derive from current ratings, optionally filtered by season.

## 6. Provider abstractions

```
providers/payment/  PaymentProvider   (DevMockPaymentProvider, <ProdProvider>)
providers/maps/     MapProvider       (DevMockMapProvider,     <ProdProvider>)
providers/email/    EmailProvider     (DevMockEmailProvider,   <ProdProvider>)
```

- Interfaces live in code; the active implementation is chosen by env.
- Dev/mock providers are **clearly labelled** in code, logs and UI, and never
  claim a real external connection.
- Services depend on the interface, never on a concrete provider.

## 7. Cross-cutting concerns

- **RBAC:** dependency + service-level checks; deny by default; server is the
  only security boundary.
- **Idempotency:** idempotency keys / natural unique constraints on join, book,
  pay, check-in, verify, MMR.
- **Audit:** `audit_logs` for admin, MMR, booking, payment and moderation
  actions (actor, action, target, metadata, timestamp).
- **Validation:** Pydantic v2 at the boundary; Zod mirrors on the client.
- **Errors:** typed errors mapped to consistent HTTP problem responses.
- **Observability:** structured logging, request IDs, health/readiness probes.
- **Security:** JWT (python-jose) + passlib hashing; secrets only via env;
  CORS locked to known origins.

## 8. Infrastructure

Docker Compose (`infra/docker-compose.yml`) runs four services:

| Service  | Image / build        | Purpose |
|----------|----------------------|---------|
| frontend | `apps/web` (Vite)    | PWA dev/preview server |
| backend  | `apps/api` (FastAPI) | API + WebSockets |
| postgres | `postgres:16`        | Durable store |
| redis    | `redis:7`            | Cache, presence, WS fan-out |

Migrations via Alembic run against Postgres. `.env.example` documents every
variable; real secrets never enter the repo.

## 9. Testing strategy

- **Backend:** pytest + httpx (async client vs ASGI app), real Postgres test DB,
  transactional fixtures. Services and endpoints covered.
- **Frontend:** Vitest + Testing Library; behaviour-first, role/label queries.
- **Contract:** `packages/shared` holds shared types/contracts to keep client and
  server in step.
