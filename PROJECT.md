# PROJECT.md — RALLY Roadmap Checklist

Legend: `[x]` done & verified · `[ ]` not started · `[~]` in progress.
A feature may only move to `[x]` when it is really implemented and its
verification command has been run with raw output captured. **No stubs.**

---

## Phase 0 — Foundations (recon, scaffold, docs)
- [x] Recon: toolchain versions captured (Python 3.11.16, Node 24.21.0, npm 11.19.0, git 2.54.0, Docker 29.8.0, Compose v5.5.1)
- [x] Git repository initialised (`main`) with `.gitignore`
- [x] Top-level docs: `README.md`, `AGENTS.md`, `PROJECT.md`, `STATUS.md`
- [x] `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/DESIGN_SYSTEM.md`, `docs/PAGE_MAP.md`
- [x] Brand config single source of truth (web `brand.ts`, api `brand.py`)
- [x] Monorepo skeleton (`apps/api`, `apps/web`, `packages/shared`, `infra`, `docs`)
- [ ] CI workflow (lint + typecheck + tests)

## Phase 1 — Backend foundation
- [x] FastAPI app factory, settings, logging (error handling: partial)
- [x] SQLAlchemy 2.0 base + session, Alembic configured (migration round-trips)
- [ ] Docker Compose: postgres, redis, backend, frontend
- [~] Health endpoint with real DB check (redis check pending)
- [ ] Auth: register/login, password hashing (passlib), JWT (python-jose), refresh
- [ ] RBAC dependency + role model, server-enforced
- [ ] `audit_logs` service and write path

## Phase 2 — Domain model & migrations
- [ ] Users, profiles, roles
- [ ] `activity_categories`, `activity_types`, `activity_configs`
- [ ] Activities, participants, waitlists
- [ ] Venues, venue availability, bookings
- [ ] Payments (provider abstraction + ledger), cost splitting
- [ ] Chat (conversations, messages) + WebSocket transport
- [ ] Check-ins, match results, result verification
- [ ] MMR: ratings, immutable `mmr_history`, leaderboards
- [ ] Reputation, achievements, tournaments, clubs

## Phase 3 — API surface
- [ ] Activities CRUD + join/leave/waitlist
- [ ] Discovery/search + filters (category, distance, time, skill)
- [ ] Venue + booking endpoints (idempotent)
- [ ] Payment + split endpoints (dev provider labelled)
- [ ] Chat endpoints + WS
- [ ] Results, verification, MMR, leaderboards
- [ ] Admin/moderation endpoints (audited)

## Phase 4 — Frontend foundation
- [ ] Vite + React 18 + TS scaffold, Tailwind, router, query client
- [ ] Brand theming (dark + light), design tokens
- [ ] Auth screens + guarded routes
- [ ] Layout shell (nav, responsive, mobile-first)
- [ ] PWA (manifest, service worker, installability)

## Phase 5 — Frontend features
- [ ] Discover feed + activity detail
- [ ] Create/join activity flows
- [ ] Booking + payment (dev provider) flows
- [ ] Chat UI (realtime)
- [ ] Check-in + result entry + verification UI
- [ ] Leaderboards, profile, reputation, achievements
- [ ] Tournaments, clubs, venue manager tools

## Phase 6 — Quality, ops, polish
- [ ] Backend tests (pytest + httpx), coverage gate
- [ ] Frontend tests (Vitest + Testing Library)
- [ ] Accessibility audit (WCAG 2.2 AA), reduced-motion
- [ ] Seed **DEMO DATA** script (clearly labelled)
- [ ] Observability, rate limiting, security review
- [ ] Docs finalised; `.env.example` complete

---

### Cross-cutting rules (always)
- Server-enforced RBAC · config-driven activity engine · immutable MMR history
- Idempotent critical flows · audited admin/MMR/booking/payment/moderation
- Provider abstractions with labelled dev/mock providers · no secrets committed
