# AGENTS.md — Engineering Conventions for RALLY

This is the contract every contributor (human or AI agent) follows. If a change
conflicts with this document, the change is wrong. **Read it before writing code.**

---

## 1. Prime directive: never fake functionality

- **No fake functionality.** No stubs masquerading as features, no "coming
  soon" placeholders for scheduled features, no hardcoded fake data in
  production flows.
- **No fake MMR, leaderboards, bookings, payments or match results.** These
  must be backed by real application state and real database rows.
- Every scheduled feature is either **really implemented and tested** or
  **absent** (tracked in `PROJECT.md`). Nothing in between.
- Seed data must be **clearly labelled DEMO DATA** (names, comments, and a
  `is_demo` flag where the domain allows).
- Never claim something works unless you ran it and can paste the raw output.
- Never pretend an external service (payments, maps, email) is connected.
  Dev/mock providers must be explicitly labelled as such.

If you cannot implement something for real yet, leave it out and record the
gap in `PROJECT.md`. Do not ship theatre.

---

## 2. Architecture rules (non-negotiable)

### 2.1 Backend layering

```
router  ->  service  ->  repository  ->  model
   (HTTP)     (logic)      (data)        (ORM)
              schemas (Pydantic v2) at the boundary
```

- Routers: parse/validate input, call a service, serialise output. **No business
  logic in route handlers.**
- Services: all business rules, transactions, orchestration. Services never
  touch the ORM session directly except through repositories.
- Repositories: data access only (SQLAlchemy 2.0 style, typed). No HTTP, no
  business rules.
- Models: SQLAlchemy declarative models. No business logic.
- Schemas: Pydantic v2. Separate `...Create`, `...Update`, `...Read` schemas.
  Never expose ORM objects directly over the API.

### 2.2 RBAC enforced server-side

- Roles: `user`, `host`, `club_organizer`, `venue_manager`,
  `tournament_organizer`, `moderator`, `admin`.
- Authorisation is enforced **in the backend** (dependency + service-level
  checks). The frontend may hide UI for UX, but is **never** the security
  boundary. Any endpoint touching a protected resource must check role/ownership
  server-side.
- Deny by default.

### 2.3 Activity engine is config-driven

- Activity behaviour comes from `activity_categories`, `activity_types` and
  `activity_configs` rows — not from `if category == "sports"` branches in
  random components.
- Adding a new activity type should be a **data/config** change, not a code
  change across the app.

### 2.4 MMR

- Activity-specific, Elo-style, transactional.
- Immutable `mmr_history` rows (append-only; corrections are new rows).
- **MMR is never accepted as input from the client.** It is computed
  server-side from verified results.
- Idempotent per verified match (re-verifying must not double-apply).

### 2.5 Provider abstractions

- Payment, map and email are interfaces with a **clearly-labelled dev/mock
  provider** and configurable production providers via env.
- Never hardcode provider SDK calls in services; go through the abstraction.

### 2.6 Idempotency & audit

- Every critical flow (join, book, pay, check-in, verify result, MMR update,
  moderation) is **idempotent** (idempotency keys / natural unique constraints).
- `audit_logs` records admin, MMR, booking, payment and moderation actions with
  actor, action, target and metadata.

---

## 3. Code style

### Backend (Python)
- Python 3.11+, `from __future__ import annotations` in modules.
- Formatting/lint: **ruff** (`ruff format` + `ruff check`). Line length 100.
- Types: **mypy** strict on `app/`. Public functions fully annotated.
- Pydantic v2 idioms (`model_config`, `field_validator`).
- SQLAlchemy 2.0 typed ORM (`Mapped[...]`, `mapped_column`).
- No bare `except:`. No mutable default arguments. No `print` in app code
  (use logging).

### Frontend (TypeScript/React)
- TypeScript `strict`. **No `any`** (use `unknown` + narrowing).
- Function components + hooks only.
- Server state via **TanStack Query**; client state via **Zustand**. Do not
  duplicate server state in Zustand.
- Forms: **React Hook Form + Zod**. Validate on the client for UX and on the
  server for truth.
- Styling: **Tailwind CSS** utility-first. No ad-hoc inline styles except for
  computed values (e.g. CSS variables from brand theme).
- Accessibility: WCAG 2.2 AA where practical — labels, focus states, keyboard
  nav, contrast, reduced-motion support.
- Mobile-first responsive: phone, tablet, iPad, desktop.

### Both
- Small, focused modules. Prefer composition over inheritance.
- Names describe intent. No abbreviations that hide meaning.

---

## 4. Testing

- **Backend:** `pytest` + `httpx` (async `AsyncClient` against the ASGI app).
  Every service method and every non-trivial endpoint gets a test. Use a real
  test database (Postgres) or a transactional fixture — not mocks of your own
  repository layer unless testing an external provider.
- **Frontend:** `vitest` + `@testing-library/react`. Test behaviour, not
  implementation. Query by role/label, not by test id, where possible.
- Bug fixes start with a failing test.
- Tests must pass locally before commit. Report the raw command + output.

Commands (planned targets):
```
# backend
cd apps/api && ruff check . && mypy app && pytest -q
# frontend
cd apps/web && npm run lint && npm run typecheck && npm run test -- --run
```

---

## 5. Commits

- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`,
  `refactor:`, `perf:`, `build:`, `ci:`.
- Scope where useful: `feat(api): ...`, `feat(web): ...`.
- Imperative mood, present tense ("add", not "added").
- One logical change per commit. Reference the batch/issue where relevant.
- **Never commit secrets.** `.env` is git-ignored; keep `.env.example` current.

Examples:
```
feat(api): add activity_categories config-driven schema
fix(web): correct MMR leaderboard pagination
docs: document provider abstraction contract
```

---

## 6. Definition of done

A change is done only when:
1. It is really implemented (no stubs, no fake data).
2. It has tests that pass (raw output available).
3. Lint + type-check pass.
4. RBAC/idempotency/audit rules above are respected where applicable.
5. Docs (`README.md`/`PROJECT.md`/`STATUS.md`/`docs/*`) are updated.
6. No secrets are committed; `.env.example` reflects new env vars.
