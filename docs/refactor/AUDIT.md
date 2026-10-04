# RALLY Sports-Only Refactor — AUDIT

Scope: RALLY pivoted from a generic "events app" to a **sports-only** social
platform. This audit records what changed, where, and the concrete evidence
(function names, model fields, line numbers) verified by reading the source.

Line numbers are from the working tree at write time and were confirmed with
`grep -n` (commands listed per section).

---

## 1. Sports catalog — single source of truth

**File:** `apps/api/app/core/sports.py` (194 lines)

| Symbol | Line | What it is |
| --- | --- | --- |
| `SPORT_CATEGORIES` | 15 | The 12 top-level sport categories (racket, team, combat, strength, running, cycling, water, winter, precision, gymnastics, outdoor, other). |
| `_S` | 30 | The raw sport rows: **111 sports**. |
| `_csv` | 157 | Splits a comma-separated catalog cell into a list. |
| `SPORTS_PAYLOAD` | 161 | Public `list[dict]` of every sport. |
| `SPORT_BY_SLUG` | 188 | `{slug: row}` lookup. |
| `SPORT_SLUGS` | 189 | `frozenset` of every slug. |
| `SPORT_CATEGORY_SLUGS` | 190 | `frozenset` of the 12 category slugs. |
| `CATEGORY_SPORTS` | 191 | `{category: [sport slugs]}`. |

Row shape (module docstring, lines 9-12): `(slug, label_id, label_en, category,
venue_kind, resource_label, competitive, variants, formats, metrics)`; the last
three are comma-separated.

Evidence — exact counts:
```
$ awk '/^_S: list/,/^]/' apps/api/app/core/sports.py | grep -cE '^    \("'
111
$ awk '/^SPORT_CATEGORIES/,/^]/' apps/api/app/core/sports.py | grep -cE '^    \("'
12
```

Each sport declares a `venue_kind` (`court`/`field`/`hall`/…) and a
`resource_label` (`Court`/`Field`/`Table`/…) the booking engine uses, plus
`competitive: bool` which gates MMR (see §4).

---

## 2. Venues are sport-aware (`venue_kind`)

**File:** `apps/api/app/models/venue.py`

- `Venue.venue_kind` — `Mapped[str | None] = mapped_column(String(40), index=True)`
  (comment: "The resource kind this venue provides … e.g. \"court\", \"field\",
  \"gym\".").
- `Venue.sport_slugs` — `Mapped[list[str]] = mapped_column(JSON, default=list,
  server_default=text("'[]'"), nullable=False)` (comment: "Sport slugs
  (app.core.sports) this venue supports.").
- `VenueCourt.venue_kind` — `String(40), index=True`.
- `VenueCourt.resource_label` — `String(60)` (the catalog `resource_label`).

So a venue advertises *which sports it can host* (`sport_slugs`) and *what kind
of resource* it is (`venue_kind`); each bookable `VenueCourt` carries the same
typing.

Projection helper: **File:** `apps/api/app/core/venue_catalog.py` — docstring
(lines 7-10) states each venue is projected into its sport slugs and typed
resources; imports `SPORTS_PAYLOAD, SPORT_BY_SLUG, SPORT_SLUGS` (line 199). An
activity-type → sport-slug map exists around line 326 and the module **fails
fast** (line 353) if the catalog references an unknown sport slug.

Evidence:
```
$ grep -n "venue_kind\|sport_slugs\|resource_label" apps/api/app/models/venue.py
$ grep -n "def \|sport\|venue_kind" apps/api/app/core/venue_catalog.py
```

---

## 3. Activities carry `sport_slug` / `sport_category`

**File:** `apps/api/app/models/activity.py`

Docstring (lines 7-11): "RALLY is sports-only: an activity names a sport from the
sports catalog … via `sport_slug` and is categorised by that sport's category …
via `sport_category`. The legacy generic `category`/`activity_type` columns are
retained for backward compatibility."

`Activity` fields:

| Field | Definition | Note |
| --- | --- | --- |
| `venue_id` | `FK venues.id, ondelete="SET NULL"` (line 78) | **retained**, nullable |
| `venue_court_id` | `FK venue_courts.id, ondelete="SET NULL"`, indexed (line 82) | specific bookable resource (sport-aware court) |
| `sport_slug` | `String(40), index=True` | sport from the catalog; nullable for legacy rows |
| `sport_category` | `pg_enum(SportCategory, "sportcategory")` | derived from `sport_slug` |
| `sport_variant` | `String(40)` | must be one of the sport's catalog `variants` |
| `sport_format` | `String(40)` | must be one of the sport's catalog `formats` |
| `sport_metrics` | `JSON` | subset of the sport's catalog `metrics` |
| `activity_type` | `String(40), index=True` | legacy generic type, retained |

`SportCategory` enum: `apps/api/app/models/enums.py:25` (RACKET, TEAM, COMBAT,
STRENGTH, RUNNING, CYCLING, WATER, WINTER, PRECISION, GYMNASTICS, OUTDOOR, OTHER).

Service layer: `apps/api/app/services/activity_service.py` — `list_activities`
accepts `sport_slug` / `sport_category` filters (lines 80-81, passed at 96-97);
`list_mine` filters by sport (line 166); `_mine_entry` resolves
`SPORT_BY_SLUG.get(activity.sport_slug)` (line 231) and loads the
`venue_court_id` court (lines 234-235); `create` resolves and stores
`sport_slug` / `sport_category` / `sport_metrics` (lines 274-284).

Evidence:
```
$ grep -n "sport_slug\|sport_category\|sport_metrics\|venue_court_id\|def " apps/api/app/services/activity_service.py
$ grep -n "class SportCategory" -A 20 apps/api/app/models/enums.py
```

---

## 4. Per-sport MMR

**File:** `apps/api/app/services/mmr_service.py` (477 lines)

Docstring (lines 13-14): "MMR is **sport-specific** (a user has one rating per
sport slug). Only catalog sports flagged `competitive=True` may change MMR."

| Symbol | Line | Purpose |
| --- | --- | --- |
| `mmr_scope_key` | 57 | Scope key: real sport → its slug (`padel`); legacy sport-less row → `category:<cat>` so they never collide. |
| `expected_score` | 72 | Elo expectation. |
| `update` | 80 | Core Elo update. |
| `provisional_k_factor` | 97 | K-factor for provisional players. |
| `team_average` | 111 | Team rating average. |
| `team_delta` | 118 | Team rating delta. |
| `score_from_scores` | 134 | Scoreline → 0/0.5/1. |
| `MmrService` | 146 | Service class. |
| `get_or_create_rating` | 153 | One row per `(user, sport_slug)`. |
| `get_user_ratings` | 182 | All of a user's per-sport ratings. |
| `apply_result` | 193 | Applies a *verified* result (idempotent); raises if the sport is non-competitive via `is_competitive_sport(sport_slug)` (line 213). |
| `_sport_for` | 283 | Resolves `(sport_slug, category)` for a match. |
| `_notify` | 299 | Sport-aware MMR notification. |
| `_leaderboard_scope` / `_ranked_ratings` | 326 / 330 | Leaderboard scoping. |
| `recompute_leaderboard` / `get_leaderboard` / `get_standing` | 343 / 381 / 416 | Leaderboards. |
| `history_for_user` | 466 | MMR history. |

Model: `apps/api/app/models/rating.py`
- `MmrRating.__table_args__` (line 40): `UniqueConstraint("user_id", "sport_slug",
  name="uq_mmr_ratings_user_sport")`.
- `MmrRating.category` (line 50) retained for back-compat; `MmrRating.sport_slug`
  (line 52) is the scope key.
- `LeaderboardEntry` (line 104): unique `(sport_slug, period, user_id)` (line 110);
  `category` (121) + `sport_slug` (123).

Gating: `is_competitive_sport` / `sport_category_slug` live in
`apps/api/app/core/sport_fields.py` (imported at mmr_service.py line 34).

Evidence:
```
$ grep -n "^def \|^class \|^async def " apps/api/app/services/mmr_service.py
$ grep -n "sport" apps/api/app/services/mmr_service.py
$ grep -n "class MmrRating\|sport_slug\|category\|UniqueConstraint" apps/api/app/models/rating.py
```

---

## 5. Clubs bound to a sport

**File:** `apps/api/app/models/club.py`

- `Club.sport_slug` — `String(40), index=True` (comment: "SPORT slug from
  `app.core.sports` (e.g. padel, running). Nullable so rows created before the
  sports pivot stay valid.").
- `Club.sport_category` — `pg_enum(SportCategory, "sportcategory")`, indexed.
- Legacy `Club.category` (`ActivityCategory` enum) retained.

Evidence:
```
$ grep -n "sport_slug\|sport_category\|class Club" apps/api/app/models/club.py
```

---

## 6. Check-in + reputation

**File:** `apps/api/app/services/checkin_service.py`

- `REP_ATTENDED_DELTA = 2` (line 39) — reputation credited on check-in.
- `REP_NO_SHOW_DELTA = -3` (line 41) — reputation debited on a no-show.
- `CheckInService` (line 44).
- `_adjust_reputation(user_id, delta)` (line 87) — mutates
  `Profile.reputation_score` (line 96) inside the current transaction.
- `check_in` (line 109) — idempotent; comment line 131 "idempotent - never
  double-applies reputation"; persists attendance and credits reputation
  atomically (line 156).
- `mark_no_show` (line 161) — sets status `NO_SHOW` and debits reputation
  (line 186).

Docstring (lines 10-12) confirms both transitions are idempotent.

Evidence:
```
$ grep -n "REP_\|def check_in\|def mark_no_show\|_adjust_reputation\|reputation" apps/api/app/services/checkin_service.py
```

---

## 7. Sport-aware notifications

**File:** `apps/api/app/services/notification_service.py`

Typed event helpers (comment line 153 "typed event helpers (sports-aware)"):
`notify_activity_joined` (166), `notify_waitlist_promoted` (193),
`notify_booking_confirmed` (217), `notify_payment_succeeded` (236),
`notify_checkin_recorded` (264), `notify_mmr_changed` (283).

Each accepts `sport_slug: str | None = None` and threads it into the
notification `data` payload (lines 187, 210, 231, 258, 278, 304).
`notify_mmr_changed` (283) labels the message with `sport_slug or category or
"your"` (line 295) — the sport-aware MMR-change notification.

Evidence:
```
$ grep -n "def notify_\|sport_slug" apps/api/app/services/notification_service.py
```

---

## 8. API surface (sport-aware)

Registered routers (`apps/api/app/api/v1/__init__.py:29-31`): `activities`,
`catalog`, `sports`. Mounted under `settings.API_V1_PREFIX`
(`apps/api/app/main.py:55`) = `"/api/v1"` (`apps/api/app/core/config.py:25`).

| Endpoint | File:line | Notes |
| --- | --- | --- |
| `GET /api/v1/sports` | `apps/api/app/api/v1/sports.py:48` | Full catalog; `?category=` and `?q=` filters. |
| `GET /api/v1/activity-types` | `apps/api/app/api/v1/catalog.py:100` | Sourced from `SPORTS_PAYLOAD`, so the create UI can only offer real sports. |
| `GET /api/v1/activities/mine` | `apps/api/app/api/v1/activities.py:105` | Router prefix `/activities` (line 32); groups upcoming/waitlisted/past/hosting. |

Evidence:
```
$ grep -n "API_V1_PREFIX" apps/api/app/core/config.py
$ grep -rn "include_router" apps/api/app/api/v1/__init__.py
$ grep -rn '"/sports"\|/activity-types\|/activities/mine' apps/api/app/api/v1/
```

---

## 9. Legacy columns retained (correction to the brief)

The refactor brief says the legacy `venue_id` was removed from activities. That
is **not** what the code shows: `Activity.venue_id` is **retained** as a nullable
`FK venues.id` (`apps/api/app/models/activity.py:78`) and the initial migration
creates it (`83302ff4ea29_initial_schema.py:264,286,295`). The sport-aware change
is *additive* — `venue_court_id` (line 82) points at the specific `venue_courts`
resource while venue-level `venue_id` stays for back-compat. `activity_type` and
the generic `category` enum are likewise retained. No migration under
`apps/api/migrations/versions/` drops `venue_id`.

Evidence:
```
$ grep -n "venue_id\|venue_court_id" apps/api/app/models/activity.py
$ grep -rn "drop_column" apps/api/migrations/versions/*.py apps/api/scripts/seed.py
```
