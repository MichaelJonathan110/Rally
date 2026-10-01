# PRODUCT_SPEC.md — RALLY Product Specification

## 1. Vision

**RALLY — "Find your people. Do more together."**

RALLY is a social activity marketplace and community platform. It turns "I want
to play / do something but have no one to do it with" into a booked, paid,
played, scored and verified activity. It spans **sports, games, outdoor, social
and creative** categories — not just sports.

RALLY is an **original** product and does not copy the code, assets, branding or
proprietary UI of any other platform (including Reclub). It may follow generic
marketplace conventions but every asset, string and screen is our own.

## 2. Problem

- People want to do activities but lack the people, venue, or organisation.
- Existing tools handle *booking* or *chat* or *scoring* — rarely the whole loop.
- Casual play has no lightweight, trustworthy way to record and verify results
  and to build reputation over time.

## 3. Target users

| Persona | Need |
|---------|------|
| **Casual player** | Find an activity near me this week, join in two taps, pay my share. |
| **Host** | Create an activity, fill the roster, collect money, check people in. |
| **Club organizer** | Run recurring sessions, manage a roster, track standings. |
| **Venue manager** | List courts/spaces, take bookings, see utilisation. |
| **Tournament organizer** | Bracket, schedule, record and verify results at scale. |
| **Moderator / Admin** | Keep the community safe; audit sensitive actions. |

## 4. Core loop

```
DISCOVER -> FIND PEOPLE -> JOIN -> BOOK -> PAY -> CHAT -> CHECK IN
        -> PARTICIPATE -> RECORD RESULT -> VERIFY -> UPDATE MMR
        -> LEADERBOARD -> REPUTATION -> DISCOVER MORE
```

Each arrow is a first-class, backed-by-real-state step:

1. **Discover** — browse/search activities by category, distance, time, skill.
2. **Find people** — see who is going, their reliability, their skill band.
3. **Join** — claim a spot (with waitlist when full). Idempotent.
4. **Book** — reserve the venue/slot for the activity. Idempotent.
5. **Pay** — pay your share or the full amount; split costs. Idempotent.
6. **Chat** — coordinate in the activity's conversation (realtime).
7. **Check in** — confirm attendance at the venue.
8. **Participate** — actually play / take part.
9. **Record result** — submit the score/outcome for the activity.
10. **Verify** — participants/opponents confirm the result.
11. **Update MMR** — activity-specific Elo update, transactional, idempotent.
12. **Leaderboard** — see where you stand, per activity.
13. **Reputation** — reliability, sportsmanship, hosting quality build up.
14. **Discover more** — better recommendations as your profile grows.

## 5. Activity categories

Config-driven (see `DATABASE.md`). Categories: `sports`, `games`, `outdoor`,
`social`, `creative`. Each category contains many **activity types** (e.g.
badminton, football, board games, hiking, book club, photography walk). Types
carry a **config** describing required fields, scoring model, MMR enablement,
team structure and capacity rules — as data, not code.

## 6. Feature areas

### 6.1 Discovery & matching
- Map + list discovery, filters (category, type, distance, time, skill, price).
- "People like you" and "activities near you" recommendations.
- Skill bands derived from MMR where the type has MMR enabled.

### 6.2 Activities
- Create (host role), recurring series, capacity, waitlist, cost, venue link.
- Join/leave, roster, attendance, check-in.
- Status lifecycle: `draft -> open -> full -> in_progress -> completed -> cancelled`.

### 6.3 Venues & booking
- Venue listings (venue_manager role), spaces/courts, availability windows.
- Booking tied to an activity, idempotent, conflict-checked.

### 6.4 Payments & cost splitting
- Provider abstraction; labelled **dev/mock** provider by default.
- Split cost equally or by custom weights; ledger of charges/settlements.
- Never fake a payment; the dev provider is explicit and non-production.

### 6.5 Chat
- Per-activity conversations, realtime via WebSockets, history persisted.

### 6.6 Results, verification & MMR
- Participants submit results; opponents/participants verify.
- On verification, MMR updates transactionally per activity type.
- Immutable `mmr_history`; MMR never accepted from the client.

### 6.7 Leaderboards & reputation
- Per activity type and per category; seasonal where configured.
- Reputation: reliability (show-ups), sportsmanship, hosting quality, fairness.

### 6.8 Tournaments & clubs
- Tournaments: brackets, scheduling, verified results, standings.
- Clubs: rosters, recurring sessions, club standings and identity.

### 6.9 Moderation & admin
- Reports, actions, bans; all sensitive actions written to `audit_logs`.

### 6.10 Achievements
- Rules-driven badges (first game, streak, verified wins, hosting milestones).

## 7. Roles & permissions (RBAC, server-enforced)

| Role | Highlights |
|------|-----------|
| `user` | Discover, join, pay, chat, check in, record/verify results, own profile. |
| `host` | Create/manage activities, manage roster, check in, collect. |
| `club_organizer` | Manage clubs, recurring sessions, club standings. |
| `venue_manager` | Manage venues/spaces/availability, view bookings. |
| `tournament_organizer` | Create/manage tournaments, brackets, results. |
| `moderator` | Handle reports, moderate content, limited account actions. |
| `admin` | Full administration; all actions audited. |

Authorisation is enforced in the backend. The UI may hide controls, but never
acts as the security boundary.

## 8. Non-functional requirements

- **Platforms:** responsive PWA — phone, tablet, iPad, desktop.
- **Performance:** fast first paint, code-split routes, cached server state.
- **Accessibility:** WCAG 2.2 AA where practical.
- **Reliability:** idempotent critical flows; auditable sensitive actions.
- **Privacy/security:** no secrets in the repo; least privilege; server-side
  validation; audit trail for admin/MMR/booking/payment/moderation.
- **Theme:** premium dark + light, restrained depth (CSS 3D/SVG).

## 9. Out of scope (for now)

- Native mobile apps (PWA first).
- Real production payment/map/email provider credentials (interfaces + labelled
  dev providers only, until configured via env).
- Any reuse of third-party proprietary UI, assets or code.
