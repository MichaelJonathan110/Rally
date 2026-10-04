# RALLY Sports-Only Refactor — MIGRATION

Schema evolution from a generic events app to sports-only. Every fact below was
confirmed by grepping the models and the Alembic migration chain; the exact
command used is quoted next to each claim.

Migrations live in `apps/api/migrations/versions/`:

| Revision | File | Down-revision |
| --- | --- | --- |
| `83302ff4ea29` | `83302ff4ea29_initial_schema.py` (63 KB) | base |
| `b1f2a3c4d5e6` | `b1f2a3c4d5e6_activity_sport_specific.py` | `83302ff4ea29` |
| `c2d3e4f5a6b7` | `c2d3e4f5a6b7_mmr_sport_specific.py` | `b1f2a3c4d5e6` |

```
$ ls -la apps/api/migrations/versions/
```

---

## 1. Venues — sport-aware columns

**Table `venues`** (`apps/api/app/models/venue.py`):

| Column | Type | Added by |
| --- | --- | --- |
| `venue_kind` | `String(40)`, indexed | `83302ff4ea29_initial_schema.py:46` (index `:261`) |
| `sport_slugs` | `JSON`, `server_default="'[]'"`, NOT NULL | `83302ff4ea29_initial_schema.py:47` |
| `province` | `String(80)`, indexed | `83302ff4ea29_initial_schema.py:7` (in-table) |
| `area` | `String(120)` | `83302ff4ea29_initial_schema.py:8` |

**Table `venue_courts`** (`apps/api/app/models/venue.py`):

| Column | Type | Added by |
| --- | --- | --- |
| `venue_kind` | `String(40)`, indexed | `83302ff4ea29_initial_schema.py:391` (index `:401`) |
| `resource_label` | `String(60)` | `83302ff4ea29_initial_schema.py:8` (in-table) |

These venue columns are already present in the **initial** schema; the
`_ensure_schema` ALTER helper in seed.py (see §4) exists for dev SQLite DBs
created *before* these columns were introduced.

```
$ grep -n "sport_slugs\|sport_slug\|sport_category\|venue_kind" apps/api/migrations/versions/83302ff4ea29_initial_schema.py
$ sed -n '/create_table(.venues./,/^    )/p' apps/api/migrations/versions/83302ff4ea29_initial_schema.py | grep -n "sa.Column"
```

---

## 2. Activities — sport fields + resource link (`b1f2a3c4d5e6`)

Migration docstring: "Adds the sports-only activity columns (sport_slug + derived
sport_category, variant/format/metrics) plus the venue_court_id resource link and
the legacy activity_type column. All are nullable, so rows created before the
sports pivot stay valid."

`upgrade()` adds to `activities`:

| Column | Type | Nullable |
| --- | --- | --- |
| `sport_slug` | `String(40)` | yes |
| `sport_category` | `sportcategory` enum | yes |
| `sport_variant` | `String(40)` | yes |
| `sport_format` | `String(40)` | yes |
| `sport_metrics` | `JSON` | yes |
| `activity_type` | `String(40)` | yes |
| `venue_court_id` | `UUID` | yes |

Indexes created: `ix_activities_sport_slug`, `ix_activities_sport_category`,
`ix_activities_activity_type`, `ix_activities_venue_court_id`.
FK created: `fk_activities_venue_court_id` → `venue_courts.id`, `ondelete="SET
NULL"`. On Postgres the `sportcategory` enum is created with `checkfirst=True`.

`downgrade()` drops the FK, the four indexes and all seven columns — it does
**not** touch `venue_id`.

Model counterpart (`apps/api/app/models/activity.py`): `venue_court_id` at line
82, `sport_slug` / `sport_category` / `sport_variant` / `sport_format` /
`sport_metrics` / `activity_type` in the `Activity` block.

```
$ cat apps/api/migrations/versions/b1f2a3c4d5e6_activity_sport_specific.py
$ grep -n "venue_id\|venue_court_id" apps/api/app/models/activity.py
```

---

## 3. MMR is per-sport (`c2d3e4f5a6b7`)

Migration docstring: "A player now has one rating per **sport slug** rather than
one per activity category." It performs three swaps.

### 3a. `mmr_ratings`
- `ADD COLUMN sport_slug String(60)` (nullable first).
- Backfill legacy rows: `UPDATE mmr_ratings SET sport_slug = 'category:' ||
  category WHERE sport_slug IS NULL` (`_LEGACY_PREFIX = "category:"`).
- `ALTER COLUMN sport_slug SET NOT NULL`; index `ix_mmr_ratings_sport_slug`.
- `DROP CONSTRAINT uq_mmr_ratings_user_category` →
  `CREATE UNIQUE uq_mmr_ratings_user_sport (user_id, sport_slug)`.

Initial definition: `mmr_ratings` had `user_id, category, rating, games_played,
wins, losses, draws` with `UniqueConstraint('user_id','category',
name='uq_mmr_ratings_user_category')` (`83302ff4ea29_initial_schema.py`, mmr
block line 15).

### 3b. `leaderboard_entries`
- `ADD COLUMN sport_slug String(60)`; backfilled `'category:' || category`.
- `SET NOT NULL`; index `ix_leaderboard_entries_sport_slug`.
- `DROP CONSTRAINT uq_leaderboard_entries_cat_period_user` →
  `CREATE UNIQUE uq_leaderboard_entries_sport_period_user (sport_slug, period,
  user_id)`.

### 3c. `mmr_history`
- `DROP CONSTRAINT uq_mmr_history_match_result` (single-column) →
  `CREATE UNIQUE uq_mmr_history_result_user (match_result_id, user_id)` — a
  composite idempotency key so team results (one history row per member) can be
  stored.

`downgrade()` reverses each step, restoring the category-scoped uniqueness.

Model counterparts (`apps/api/app/models/rating.py`): `MmrRating` unique
`(user_id, sport_slug)` at line 40; `LeaderboardEntry` unique `(sport_slug,
period, user_id)` at line 110.

```
$ sed -n '50,120p' apps/api/migrations/versions/c2d3e4f5a6b7_mmr_sport_specific.py
$ grep -n "class MmrRating\|sport_slug\|UniqueConstraint" apps/api/app/models/rating.py
```

---

## 4. Idempotent ALTER helper in seed.py

**File:** `apps/api/scripts/seed.py` — `def _ensure_schema(engine)` (line 96).

Docstring (lines 99-101): "`create_all` never ALTERs existing tables, so a dev DB
created before the province/area columns existed would fail. This is a no-op on
Postgres." It returns early unless `DATABASE_URL.startswith("sqlite")`.

It reads live columns via `PRAGMA table_info(...)` and only issues an
`ALTER TABLE ... ADD COLUMN` when the column is absent — hence idempotent:

| Table | Column | Statement | Line |
| --- | --- | --- | --- |
| `venues` | `province` | `ALTER TABLE venues ADD COLUMN province VARCHAR(80)` | 107 |
| `venues` | `area` | `ALTER TABLE venues ADD COLUMN area VARCHAR(120)` | 109 |
| `venues` | `venue_kind` | `ALTER TABLE venues ADD COLUMN venue_kind VARCHAR(40)` | 111 |
| `venues` | `sport_slugs` | `ALTER TABLE venues ADD COLUMN sport_slugs JSON DEFAULT '[]'` | 114 |
| `venue_courts` | `venue_kind` | `ALTER TABLE venue_courts ADD COLUMN venue_kind VARCHAR(40)` | 121 |
| `venue_courts` | `resource_label` | `ALTER TABLE venue_courts ADD COLUMN resource_label VARCHAR(60)` | 125 |

Guard pattern:
```python
cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(venues)")}
if "venue_kind" not in cols:
    conn.exec_driver_sql("ALTER TABLE venues ADD COLUMN venue_kind VARCHAR(40)")
```

The seed also writes `sport_slugs` per venue (lines 198-205, 295) and scopes
legacy demo ratings as `category:<cat>` (`_seed_ratings`, ~line 456) so they stay
distinct under the new `(user_id, sport_slug)` unique key. It prints "Seed is
idempotent: re-running creates nothing new." (line 545).

```
$ grep -n "ALTER\|def _ensure\|PRAGMA\|table_info\|idempot" apps/api/scripts/seed.py
$ sed -n '96,130p' apps/api/scripts/seed.py
```

---

## 5. Legacy `venue_id` — retained, NOT removed

Contrary to the brief, `activities.venue_id` was **not** removed. It is created in
the initial schema (`83302ff4ea29_initial_schema.py:264` column, `:286` FK, `:295`
index) and still exists on the model (`apps/api/app/models/activity.py:78`). The
sport-aware change is additive: `venue_court_id` (line 82) points at a specific
`venue_courts` row while venue-level `venue_id` remains for back-compat.

```
$ grep -rn "drop_column" apps/api/migrations/versions/*.py apps/api/scripts/seed.py
# -> only sport_* / venue_court_id / activity_type / sport_slug drops appear,
#    never venue_id
$ grep -n "venue_id\|venue_court_id" apps/api/app/models/activity.py
# 78: venue_id  ...  82: venue_court_id
```

---

## 6. Column/table change summary

| Object | Change | Migration |
| --- | --- | --- |
| `venues.venue_kind` | add (indexed) | 83302ff4ea29 |
| `venues.sport_slugs` | add JSON default `[]` | 83302ff4ea29 |
| `venues.province`, `venues.area` | add | 83302ff4ea29 |
| `venue_courts.venue_kind` | add (indexed) | 83302ff4ea29 |
| `venue_courts.resource_label` | add | 83302ff4ea29 |
| `activities.sport_slug` | add (indexed) | b1f2a3c4d5e6 |
| `activities.sport_category` | add enum `sportcategory` (indexed) | b1f2a3c4d5e6 |
| `activities.sport_variant` | add | b1f2a3c4d5e6 |
| `activities.sport_format` | add | b1f2a3c4d5e6 |
| `activities.sport_metrics` | add JSON | b1f2a3c4d5e6 |
| `activities.activity_type` | add (indexed) | b1f2a3c4d5e6 |
| `activities.venue_court_id` | add UUID FK → venue_courts | b1f2a3c4d5e6 |
| `mmr_ratings.sport_slug` | add, backfill `category:*`, NOT NULL | c2d3e4f5a6b7 |
| `mmr_ratings` unique | `(user_id, category)` → `(user_id, sport_slug)` | c2d3e4f5a6b7 |
| `leaderboard_entries.sport_slug` | add, backfill, NOT NULL | c2d3e4f5a6b7 |
| `leaderboard_entries` unique | `(category, period, user_id)` → `(sport_slug, period, user_id)` | c2d3e4f5a6b7 |
| `mmr_history` unique | `(match_result_id)` → `(match_result_id, user_id)` | c2d3e4f5a6b7 |
| `activities.venue_id` | **unchanged / retained** | — |
