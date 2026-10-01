# DATABASE.md — RALLY Data Model

PostgreSQL is the source of truth. SQLAlchemy 2.0 typed models; Alembic
migrations. All tables carry `id` (UUID), `created_at`, `updated_at`. Soft
delete via `deleted_at` where retention matters. Money is stored as integer
**minor units** (e.g. cents) with an ISO-4217 `currency` code.

Conventions:
- UUID primary keys (`uuid` / `gen_random_uuid()`).
- Timestamps `timestamptz`, UTC.
- FKs explicit with `ON DELETE` behaviour chosen deliberately.
- Enum-like columns use Postgres enums or constrained text; domain enums live
  in code and mirror the DB.
- Every table that participates in an audited flow is referenced by `audit_logs`.

---

## 1. Identity and access

### users
| column | type | notes |
|--------|------|-------|
| id | uuid pk | |
| email | citext unique | login identifier |
| password_hash | text | passlib hash; never returned |
| display_name | text | |
| status | text | `active`, `suspended`, `deleted` |
| is_demo | boolean | DEMO DATA marker |
| created_at / updated_at | timestamptz | |

### roles / user_roles
- `roles(id, key, description)` seeded with `user, host, club_organizer,
  venue_manager, tournament_organizer, moderator, admin`.
- `user_roles(user_id, role_id, granted_by, granted_at)` — many-to-many; the
  effective permission set is the union, evaluated **server-side**.

### profiles
`user_id pk/fk`, `bio`, `avatar_url`, `location` (lat/lng), `city`,
`preferred_categories` (text[]), `skill_bands` (jsonb per activity_type).

### audit_logs
| column | type | notes |
|--------|------|-------|
| id | uuid pk | |
| actor_user_id | uuid fk users | who |
| action | text | e.g. `mmr.update`, `booking.create` |
| target_type / target_id | text / uuid | what |
| metadata | jsonb | redacted payload |
| ip / user_agent | text | |
| created_at | timestamptz | append-only |

---

## 2. Activity engine (config-driven)

### activity_categories
`id, key (sports|games|outdoor|social|creative), name, description, icon,
sort_order, is_active`.

### activity_types
`id, category_id fk, key, name, description, icon, is_active`.
Unique `(category_id, key)`.

### activity_configs
Per-type behaviour as **data**, not code:
| column | type | notes |
|--------|------|-------|
| activity_type_id | uuid fk unique | |
| required_fields | jsonb | dynamic form schema |
| scoring_model | text | none / sets / score / custom |
| mmr_enabled | boolean | |
| team_structure | jsonb | singles/teams/sides |
| min_players / max_players | int | |
| waitlist_enabled | boolean | |
| verification_policy | text | none / opponent / majority / host |
| extra | jsonb | forward-compatible |

Adding an activity type = inserting rows here. No app-code branching on
category.

---

## 3. Activities and participation

### activities
| column | type | notes |
|--------|------|-------|
| id | uuid pk | |
| host_user_id | uuid fk users | |
| activity_type_id | uuid fk | |
| venue_id | uuid fk venues null | |
| title / description | text | |
| starts_at / ends_at | timestamptz | |
| capacity | int | |
| price_minor / currency | int / text | |
| status | text | draft / open / full / in_progress / completed / cancelled |
| visibility | text | public / club / invite |
| recurrence_rule | text null | iCal RRULE for series |
| is_demo | boolean | |

### activity_participants
`activity_id, user_id, role (participant|host|substitute), status
(invited|joined|waitlisted|checked_in|attended|no_show|cancelled),
joined_at`. Unique `(activity_id, user_id)`. Idempotent join via this
constraint + idempotency key.

### check_ins
`activity_id, user_id, checked_in_at, method (qr|manual|geofence), verified_by`.
Unique `(activity_id, user_id)`.

---

## 4. Venues and booking

### venues
`id, owner_user_id, name, description, address, location (lat/lng), amenities
jsonb, is_active, is_demo`.

### venue_spaces
`id, venue_id, name, activity_type_ids (uuid[]), capacity, price_minor,
currency`.

### venue_availability
`id, space_id, weekday, start_time, end_time, valid_from, valid_to`.

### bookings
| column | type | notes |
|--------|------|-------|
| id | uuid pk | |
| activity_id | uuid fk | |
| space_id | uuid fk | |
| starts_at / ends_at | timestamptz | |
| status | text | held / confirmed / cancelled / completed |
| idempotency_key | text unique | **idempotent booking** |
| total_minor / currency | int / text | |
| is_demo | boolean | |

Conflict check on `(space_id, time range)` performed server-side in a
transaction.

---

## 5. Payments and cost splitting

### payments
`id, activity_id, payer_user_id, amount_minor, currency, status
(pending|authorized|captured|refunded|failed), provider (dev_mock|...),
provider_ref, idempotency_key unique, is_demo, created_at`.

### payment_splits
`id, activity_id, user_id, share_minor, status (pending|paid|waived),
payment_id null`. Sum of shares equals activity total (enforced in service).

### ledger_entries
`id, user_id, activity_id, direction (debit|credit), amount_minor, currency,
ref, created_at` — append-only money movement for reconciliation.

> The **dev/mock** payment provider is explicitly labelled everywhere and never
> claims a real capture. Production providers are selected via env.

---

## 6. Chat

### conversations
`id, activity_id null, club_id null, kind (activity|club|direct), created_at`.

### conversation_members
`conversation_id, user_id, joined_at, last_read_at`. Unique pair.

### messages
`id, conversation_id, sender_user_id, body, attachments jsonb, created_at,
edited_at, deleted_at`. Realtime fan-out via Redis + WebSocket.

---

## 7. Results, verification and MMR

### match_results
| column | type | notes |
|--------|------|-------|
| id | uuid pk | |
| activity_id | uuid fk | |
| submitted_by | uuid fk users | |
| payload | jsonb | scores/outcomes per scoring_model |
| status | text | submitted / verified / disputed / rejected |
| is_demo | boolean | |

### result_verifications
`id, match_result_id, verifier_user_id, decision (confirm|dispute),
comment, created_at`. Unique `(match_result_id, verifier_user_id)`.

### mmr_ratings
Current rating per user per activity type:
`id, user_id, activity_type_id, rating (int, e.g. Elo), matches_played,
wins, losses, draws, updated_at`. Unique `(user_id, activity_type_id)`.

### mmr_history (immutable, append-only)
| column | type | notes |
|--------|------|-------|
| id | uuid pk | |
| user_id | uuid fk | |
| activity_type_id | uuid fk | |
| match_result_id | uuid fk | source |
| rating_before / rating_after | int | |
| delta | int | |
| algorithm | text | e.g. `elo_v1` |
| created_at | timestamptz | |

**Idempotency:** unique `(match_result_id, user_id, activity_type_id)` (or an
idempotency key) guarantees a verified result applies MMR exactly once. MMR is
**never** accepted as client input.

### seasons / leaderboard snapshots
`seasons(id, activity_type_id, name, starts_at, ends_at)`;
`leaderboard_snapshots(id, season_id, activity_type_id, user_id, rank, rating,
captured_at)` for historical standings.

---

## 8. Reputation, achievements, clubs, tournaments

### reputation_events
`id, user_id, kind (attended|no_show|host_rating|fair_play|report), weight,
ref_type, ref_id, created_at` -> aggregated into reputation scores.

### achievements / user_achievements
`achievements(id, key, name, description, rule jsonb)`;
`user_achievements(user_id, achievement_id, earned_at)` unique pair.

### clubs / club_members
`clubs(id, name, owner_user_id, activity_type_ids, is_demo)`;
`club_members(club_id, user_id, role, joined_at)` unique pair.

### tournaments
`tournaments(id, organizer_user_id, activity_type_id, name, format
(knockout|league|round_robin), starts_at, status, is_demo)`;
`tournament_participants`, `tournament_matches(id, tournament_id, round,
slot, participant_a, participant_b, match_result_id null, status)`.

---

## 9. Moderation

### reports
`id, reporter_user_id, target_type (user|activity|message|venue),
target_id, reason, details, status (open|reviewing|actioned|dismissed),
handled_by, created_at`.

### moderation_actions
`id, moderator_user_id, target_type, target_id, action (warn|hide|suspend|ban),
reason, expires_at, created_at` -> also written to `audit_logs`.

---

## 10. Integrity rules (enforced in services/DB)

- Activity `capacity` respected on join; overflow -> waitlist.
- Booking and payment flows are **idempotent** (unique idempotency keys).
- `mmr_history` is **append-only**; corrections add new rows.
- MMR update is **transactional** with result verification.
- Every admin/MMR/booking/payment/moderation action writes an `audit_logs` row.
- Payment split shares sum to the activity total.
- DEMO DATA rows are flagged `is_demo` and clearly labelled in seeds.
