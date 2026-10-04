# RALLY Sports-Only Refactor — VERIFY

How to verify the sports-only refactor: the exact commands and their expected
green output, plus the key endpoints.

Repo root: `C:/Users/kohja/rally`. Shell: bash (Git Bash). The API has its own
virtualenv at `apps/api/.venv`; the web app is a Node/Vite project at `apps/web`.

---

## 1. Backend tests (pytest)

Config (`apps/api/pyproject.toml`):

```
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
asyncio_mode = "auto"
```

Test suite: 20 test modules in `apps/api/tests/`, including `test_activities.py`,
`test_venues.py`, `test_mmr.py`, `test_checkin.py`, `test_clubs.py`,
`test_notifications.py`, `test_bookings.py`, `test_models.py`.

Run:

```bash
cd apps/api
./.venv/Scripts/python.exe -m pytest -q
```

Expected (green) output - quiet mode, all pass:

```
..................................................s.................. [100%]
NNN passed, M skipped in X.XXs
```

Focused run for the sport-aware areas:

```bash
./.venv/Scripts/python.exe -m pytest tests/test_mmr.py tests/test_activities.py tests/test_venues.py tests/test_checkin.py tests/test_clubs.py tests/test_notifications.py -q
```

Evidence:

```
$ grep -n "pytest\|testpaths\|addopts\|asyncio" apps/api/pyproject.toml
$ ls apps/api/tests/*.py | wc -l
20
```

---

## 2. Frontend typecheck + tests (tsc / vitest)

Scripts (`apps/web/package.json`): `"build": "tsc --noEmit && vite build"`,
`"preview": "vite preview"`, `"typecheck": "tsc --noEmit"`, `"test": "vitest"`.

Typecheck (a clean `tsc --noEmit` prints nothing and exits 0):

```bash
cd apps/web
npm run typecheck
# expected: (no output), exit code 0
```

Unit tests:

```bash
npm test
# expected: Test Files  N passed (N) / Tests  N passed (N)
```

Evidence:

```
$ grep -n "\"preview\"\|\"build\"\|\"typecheck\"\|\"test\"" apps/web/package.json
```

---

## 3. Boot the app

### 3a. Backend - uvicorn (SQLite), port 8001

The project ships a launcher `apps/api/scripts/serve_sqlite.py` that runs uvicorn
against the SQLite DB. `start-rally.ps1` (lines 19-25) starts it with
`apps/api/.venv/Scripts/python.exe scripts/serve_sqlite.py` on **port 8001**.

```bash
cd apps/api
./.venv/Scripts/python.exe scripts/serve_sqlite.py
```

Expected: logs `Application startup complete.` and `Uvicorn running on
http://127.0.0.1:8001`. The FastAPI app is created in `apps/api/app/main.py` and
mounts `api_router` under `settings.API_V1_PREFIX` (main.py:55), which is
`"/api/v1"` (config.py:25).

Health check:

```bash
curl -s http://127.0.0.1:8001/api/v1/health
```

### 3b. Frontend - Vite preview on :4173

Vite config (`apps/web/vite.config.ts:73`): `preview: { port: 4173, host: true }`.
`start-rally.ps1` (lines 27-35) runs `npm run preview -- --port 4173 --host
127.0.0.1` from `apps/web`.

```bash
cd apps/web
npm run preview -- --port 4173 --host 127.0.0.1
```

Expected:

```
  ->  Local:   http://127.0.0.1:4173/
```

---

## 4. Key endpoints (sports-only)

| Endpoint | Method | Handler | What it proves |
| --- | --- | --- | --- |
| `/api/v1/sports` | GET | `apps/api/app/api/v1/sports.py:49` `list_sports` | Full sports catalog (111 sports / 12 categories); supports `?category=` and `?q=`. |
| `/api/v1/activity-types` | GET | `apps/api/app/api/v1/catalog.py:101` `list_activity_types` | Returns the same sports (slug + labels + sport category) so the create UI can only offer real sports. |
| `/api/v1/activities/mine` | GET | `apps/api/app/api/v1/activities.py:106` `list_my_activities` (router prefix `/activities`, line 32) | Sport-aware "my activities" (groups upcoming/waitlisted/past/hosting); requires auth. |

Routers are registered in `apps/api/app/api/v1/__init__.py:29-31` (`activities`,
`catalog`, `sports`).

Smoke checks:

```bash
# 111 sports expected
curl -s http://127.0.0.1:8001/api/v1/sports | ./apps/api/.venv/Scripts/python.exe -c "import sys,json;print(len(json.load(sys.stdin)))"

# category filter works
curl -s "http://127.0.0.1:8001/api/v1/sports?category=racket"

# activity-types mirrors the catalog
curl -s http://127.0.0.1:8001/api/v1/activity-types | ./apps/api/.venv/Scripts/python.exe -c "import sys,json;print(len(json.load(sys.stdin)))"

# mine (needs a bearer token)
curl -s -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8001/api/v1/activities/mine
```

Note: on this Windows host the bare `python`/`python3` on PATH is the Microsoft
Store stub, so use the venv interpreter for JSON parsing too.

Evidence:

```
$ grep -n "API_V1_PREFIX" apps/api/app/core/config.py        # -> 25: "/api/v1"
$ grep -n "include_router" apps/api/app/api/v1/__init__.py   # -> activities, catalog, sports
$ grep -n "def list_sports" apps/api/app/api/v1/sports.py
$ grep -n "def list_activity_types" apps/api/app/api/v1/catalog.py
$ grep -n "def list_my_activities" apps/api/app/api/v1/activities.py
$ grep -n "preview" apps/web/vite.config.ts                  # -> 73: preview port 4173
$ grep -n "uvicorn\|preview\|4173\|8001" start-rally.ps1
```

---

## 5. What could NOT be fully verified here

- **No live test run.** Per the job constraints (no vite build, no alembic, no
  seed, no servers), pytest/tsc were **not executed**; the expected green output
  above is the documented shape from the configs (`pyproject.toml`,
  `package.json`), not an observed run.
- **Exact pass/skip counts** are therefore unknown; run the commands in sections
  1-2 to capture them.
- `serve_sqlite.py` contents were not inspected line-by-line; the port 8001 /
  uvicorn claim is sourced from `start-rally.ps1` lines 19-25.
