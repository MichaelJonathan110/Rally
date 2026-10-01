# PAGE_MAP.md — RALLY Page Map & Routes

Every route maps to a real screen backed by real state. Auth-required routes are
guarded; role-gated routes are enforced **server-side** (UI gating is UX only).

Legend: **Public** = no auth · **Auth** = signed-in · **Role** = requires a role.

---

## 1. Public

| Path | Screen | Notes |
|------|--------|-------|
| `/` | Landing / Discover (signed-out) | Value prop, search entry, trending activities (real data). |
| `/discover` | Discover feed | Map + list, filters (category, distance, time, skill, price). |
| `/activities/:id` | Activity detail (read) | Public activities visible signed-out; join prompts sign-in. |
| `/venues/:id` | Venue detail (read) | Spaces, availability, location. |
| `/leaderboards` | Leaderboards (public view) | Per activity type / category. |
| `/leaderboards/:activityTypeKey` | Leaderboard detail | Rank, rating, season filter. |
| `/users/:handle` | Public profile | Reputation, achievements, verified stats. |
| `/login` | Sign in | |
| `/register` | Sign up | |
| `/forgot-password` | Request reset | |
| `/reset-password` | Reset with token | |
| `/legal/terms`, `/legal/privacy` | Legal | |

---

## 2. Authenticated (any signed-in user)

| Path | Screen | Notes |
|------|--------|-------|
| `/home` | Personal home | Your next activities, invites, notifications, MMR snapshot. |
| `/activities/new` | Create activity | Config-driven form from activity_configs. |
| `/activities/:id/edit` | Edit activity | Host/owner only (server-enforced). |
| `/activities/:id/chat` | Activity chat | Realtime. |
| `/activities/:id/check-in` | Check in | QR / manual / geofence. |
| `/activities/:id/result` | Record result | Dynamic form per scoring_model. |
| `/activities/:id/verify` | Verify result | Participants/opponents. |
| `/my/activities` | My activities | Hosting, joined, past. |
| `/my/bookings` | My bookings | Upcoming, past, receipts. |
| `/my/payments` | Payments | Charges, splits, settlements. |
| `/my/mmr` | My ratings | Per activity type + history chart. |
| `/my/reputation` | Reputation | Reliability, sportsmanship, hosting. |
| `/my/achievements` | Achievements | Earned + progress. |
| `/my/profile` | Edit profile | Bio, location, preferences, skill bands. |
| `/my/settings` | Settings | Theme, notifications, account, sessions. |
| `/notifications` | Notifications | Invites, verifications, reminders. |
| `/search` | Global search | Activities, people, venues, clubs. |

---

## 3. Role-gated areas

### Host (`host`)
| Path | Screen |
|------|--------|
| `/host/activities` | Manage your activities |
| `/host/activities/:id/roster` | Roster, waitlist, attendance, check-in control |
| `/host/activities/:id/collect` | Cost split + payment status |

### Club organizer (`club_organizer`)
| Path | Screen |
|------|--------|
| `/clubs` | Club directory |
| `/clubs/:id` | Club home (sessions, roster, standings) |
| `/clubs/:id/manage` | Manage club, members, recurring sessions |
| `/clubs/new` | Create club |

### Venue manager (`venue_manager`)
| Path | Screen |
|------|--------|
| `/venues/mine` | My venues |
| `/venues/new` | Create venue |
| `/venues/:id/manage` | Venue details, spaces, availability |
| `/venues/:id/bookings` | Bookings + utilisation |

### Tournament organizer (`tournament_organizer`)
| Path | Screen |
|------|--------|
| `/tournaments` | Tournament directory |
| `/tournaments/new` | Create tournament (format, schedule) |
| `/tournaments/:id` | Public tournament page (bracket/standings) |
| `/tournaments/:id/manage` | Brackets, scheduling, results, verification |

### Moderator (`moderator`)
| Path | Screen |
|------|--------|
| `/mod/reports` | Report queue |
| `/mod/reports/:id` | Report detail + actions |
| `/mod/actions` | Moderation action log |

### Admin (`admin`)
| Path | Screen |
|------|--------|
| `/admin` | Admin overview |
| `/admin/users` | Users, roles, suspensions |
| `/admin/activities` | Activities oversight |
| `/admin/venues` | Venues oversight |
| `/admin/payments` | Payments oversight |
| `/admin/mmr` | MMR inspection + corrections (audited) |
| `/admin/activity-engine` | Manage categories/types/configs (config-driven) |
| `/admin/moderation` | Reports + actions |
| `/admin/audit` | Audit log browser |

---

## 4. Shared / system

| Path | Screen |
|------|--------|
| `*` | Not found (404) |
| `/error` | Error boundary fallback |
| `/offline` | PWA offline fallback |
| `/onboarding` | First-run profile + preferences |

---

## 5. Navigation model

- **Mobile:** bottom tab bar — Discover · Home · Create (center) · My activities
  · Profile. Bottom sheet for filters and actions.
- **Desktop/iPad:** top bar — brand, Discover, Leaderboards, Tournaments, Clubs,
  search, notifications, avatar menu. Left rail for role areas.
- Role areas appear only when the user holds the role (UX); the backend still
  authorises every call.

## 6. Route guards

- **Public** routes render for anyone; actions prompt sign-in.
- **Auth** routes require a valid session (redirect to `/login?next=`).
- **Role** routes require the role; the backend rejects unauthorised calls with
  `403` regardless of what the client renders.
- Data-fetching uses TanStack Query with per-route caches; mutations invalidate
  affected queries (activities, bookings, payments, mmr, leaderboards).
