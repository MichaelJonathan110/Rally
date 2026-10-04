"""Self-refreshing demo events ("kegiatan").

Guarantees the app always shows *today + the next 13 days*: for every date in
that window at least two public, upcoming activities exist, with start times
spread across the day (morning / afternoon / evening). The refresh is:

* **idempotent** - a deterministic title per ``(date, slot)`` is checked before
  insert, so running it repeatedly never duplicates rows;
* **safe** - it reuses existing demo users / venues / clubs (never invents FK
  ids) and is wrapped by the caller so it can never crash startup or a request;
* **self-pruning** - only its *own* generated rows (``is_demo`` + the
  ``RALLY .`` title tag) older than ~3 days are removed; hand-seeded data is
  left untouched.

Mirrors the self-heal spirit of ``scripts/serve_sqlite.py::reconcile_schema``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.sport_fields import activity_category_for_sport
from app.core.sports import SPORT_BY_SLUG
from app.models.activity import Activity, ActivityParticipant
from app.models.club import Club
from app.models.enums import ActivityVisibility, ParticipantStatus, SkillLevel, UserRole
from app.models.user import User
from app.models.venue import Venue

logger = logging.getLogger("rally.events")

#: Jakarta is UTC+7 all year (no DST) - a fixed offset avoids any tzdata dep.
JAKARTA = timezone(timedelta(hours=7))
#: Days of guaranteed coverage, starting today.
WINDOW_DAYS = 14
#: Marker prefixed to every generated title so only *our* rows are ever pruned.
AUTO_TAG = "RALLY \u2022 "
#: Generated rows older than this are pruned (hand-seeded rows never are).
PRUNE_AFTER_DAYS = 3
#: Today's events must start at least this far in the future.
LEAD_TIME = timedelta(minutes=90)
#: Hours between background refresh runs (the loop in ``app.main``).
REFRESH_INTERVAL_HOURS = 6
#: Hard guarantee: never fewer than this many upcoming events per day.
MIN_PER_DAY = 2
#: Aim: a full morning / afternoon / evening spread per day.
TARGET_PER_DAY = 3

#: Sports cycled through the generated events (realistic RALLY activities).
SPORTS: tuple[str, ...] = (
    "running",
    "badminton",
    "futsal",
    "football",
    "calisthenics",
    "road-cycling",
    "hiking",
    "basketball",
    "trail-running",
    "padel",
    "tennis",
    "mountaineering",
)


@dataclass(frozen=True)
class _Slot:
    key: str
    label: str
    hour: int
    minute: int


#: Start slots spread morning -> evening (Jakarta wall-clock).
SLOTS: tuple[_Slot, ...] = (
    _Slot("pagi", "Sesi Pagi", 6, 30),
    _Slot("siang", "Sesi Siang", 10, 0),
    _Slot("sore", "Sesi Sore", 15, 30),
    _Slot("petang", "Sesi Petang", 17, 30),
    _Slot("malam", "Sesi Malam", 19, 30),
    _Slot("malam2", "Sesi Malam 2", 21, 0),
)

#: Slot indexes used on future days: pagi (morning), sore (afternoon),
#: malam (evening) - a visible spread across the whole day.
FUTURE_SLOT_INDEXES: tuple[int, ...] = (0, 2, 4)


def _slot_start(d: date, slot: _Slot) -> datetime:
    """Aware UTC datetime for a slot on a Jakarta calendar date."""
    local = datetime.combine(d, time(slot.hour, slot.minute), tzinfo=JAKARTA)
    return local.astimezone(UTC)


def _jakarta_date(moment: datetime) -> date:
    """The Jakarta calendar date for an aware ``moment``."""
    return moment.astimezone(JAKARTA).date()


def _sport_for(d: date, slot_index: int) -> str:
    """Deterministic sport for ``(date, slot)`` - independent of *when* it runs."""
    return SPORTS[(d.toordinal() + slot_index) % len(SPORTS)]


def _title_for(d: date, label: str, sport: str) -> str:
    """Stable title for a generated event (the idempotency key)."""
    return f"{AUTO_TAG}{SPORT_BY_SLUG[sport]['label_id']} {label} \u2022 {d.isoformat()}"


def _pick_host(session: Session) -> User | None:
    """An existing demo user to own generated events (prefers the HOST role)."""
    users = session.scalars(select(User).where(User.is_demo.is_(True))).all()
    if not users:
        users = session.scalars(select(User)).all()
    if not users:
        return None
    for user in users:
        if str(getattr(user, "role", "")) == str(UserRole.HOST):
            return user
    return users[0]


def _venue_slugs(venue: Venue) -> list[str]:
    """Normalise the ``venues.sport_slugs`` JSON column to a list of slugs."""
    raw = getattr(venue, "sport_slugs", None)
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except ValueError:
            return []
        return [str(x) for x in parsed] if isinstance(parsed, list) else []
    return []


def _venue_pools(session: Session) -> tuple[dict[str, list[Venue]], list[Venue]]:
    """Index existing venues by sport slug (falls back to every venue)."""
    venues = list(session.scalars(select(Venue).where(Venue.is_demo.is_(True))).all())
    if not venues:
        venues = list(session.scalars(select(Venue)).all())
    index: dict[str, list[Venue]] = {}
    for venue in venues:
        for slug in _venue_slugs(venue):
            index.setdefault(slug, []).append(venue)
    return index, venues


def _create_event(
    session: Session,
    host: User,
    venue_pools: dict[str, list[Venue]],
    all_venues: list[Venue],
    club_by_sport: dict[str, Club],
    sport: str,
    title: str,
    start: datetime,
) -> Activity:
    """Insert one generated activity plus its host participation row."""
    row = SPORT_BY_SLUG[sport]
    sport_category = str(row["category"])
    pool = venue_pools.get(sport) or all_venues
    venue = pool[start.toordinal() % len(pool)] if pool else None
    club = club_by_sport.get(sport)
    activity = Activity(
        host_id=host.id,
        venue_id=venue.id if venue is not None else None,
        club_id=club.id if club is not None else None,
        title=title,
        description=(
            f"Sesi komunitas {row['label_id']} di "
            f"{venue.name if venue is not None else 'lokasi komunitas'}. "
            "Terbuka untuk semua level - ayo bergabung!"
        ),
        category=activity_category_for_sport(sport_category),
        skill_level=SkillLevel.ANY,
        visibility=ActivityVisibility.PUBLIC,
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        max_participants=20 if sport_category == "team" else 12,
        cost_per_person_cents=50_000 + (start.toordinal() % 5) * 15_000,
        currency="IDR",
        sport_slug=sport,
        sport_category=sport_category,
        is_demo=True,
    )
    session.add(activity)
    session.flush()
    session.add(
        ActivityParticipant(
            activity_id=activity.id,
            user_id=host.id,
            status=ParticipantStatus.CONFIRMED,
            is_host=True,
            joined_at=datetime.now(UTC),
        )
    )
    return activity


def _candidates(now: datetime, today: date) -> list[tuple[date, int, str, str, datetime]]:
    """Every ``(date, slot_index, slot_key, label, start)`` we want populated.

    Future days get three spread slots; *today* only keeps slots still at least
    ``LEAD_TIME`` away (never an already-past event), topping up with near-term
    extras if fewer than two remain.
    """
    out: list[tuple[date, int, str, str, datetime]] = []
    for offset in range(WINDOW_DAYS):
        d = today + timedelta(days=offset)
        if offset == 0:
            future = [
                (i, slot) for i, slot in enumerate(SLOTS) if _slot_start(d, slot) >= now + LEAD_TIME
            ]
            for i, slot in future:
                out.append((d, i, slot.key, slot.label, _slot_start(d, slot)))
            if len(future) < 2:
                for extra in (2, 4):
                    out.append(
                        (
                            d,
                            90 + extra,
                            f"extra{extra}",
                            f"Sesi Tambahan {extra}",
                            now + timedelta(hours=extra),
                        )
                    )
        else:
            # A morning / afternoon / evening session on every future day,
            # so the window never collapses into a single block of mornings.
            for i in FUTURE_SLOT_INDEXES:
                slot = SLOTS[i]
                out.append((d, i, slot.key, slot.label, _slot_start(d, slot)))
    return out


def _upcoming_on(session: Session, d: date, now: datetime) -> int:
    """Count still-upcoming, non-cancelled events on Jakarta date ``d``.

    For *today* an event only counts when it starts at least ``LEAD_TIME`` from
    now, matching what :func:`_candidates` is willing to generate.
    """
    floor = now + LEAD_TIME if d == _jakarta_date(now) else _slot_start(d, SLOTS[0])
    lo = _slot_start(d, SLOTS[0])
    hi = lo + timedelta(days=1)
    return int(
        session.scalar(
            select(func.count())
            .select_from(Activity)
            .where(
                Activity.is_cancelled.is_(False),
                Activity.starts_at >= max(lo, floor),
                Activity.starts_at < hi,
            )
        )
        or 0
    )


def ensure_upcoming_events(session: Session) -> int:
    """Ensure >=2 upcoming activities on each of the next ``WINDOW_DAYS`` days.

    Per date, existing still-upcoming events are counted first; only enough
    generated slots are added to reach the floor of two. Each insert is also
    guarded by its deterministic title, so the call is idempotent even if it is
    interrupted midway. Never raises for missing reference data: with no users
    available it simply creates nothing.
    """
    host = _pick_host(session)
    if host is None:
        logger.info("event refresh skipped: no users available to host demo events")
        return 0
    venue_pools, all_venues = _venue_pools(session)
    club_by_sport = {c.sport_slug: c for c in session.scalars(select(Club)).all() if c.sport_slug}

    now = datetime.now(UTC)
    today = now.astimezone(JAKARTA).date()

    # Group the desired slots per date so we can top each day up independently.
    by_date: dict[date, list[tuple[int, str, str, datetime]]] = {}
    for d, slot_index, key, label, start in _candidates(now, today):
        by_date.setdefault(d, []).append((slot_index, key, label, start))

    created = 0
    for d in sorted(by_date):
        # Top the day up to the full spread; the MIN_PER_DAY floor is
        # satisfied because TARGET_PER_DAY (3) > MIN_PER_DAY (2).
        need = TARGET_PER_DAY - _upcoming_on(session, d, now)
        if need <= 0:
            continue
        for slot_index, _key, label, start in by_date[d]:
            if need <= 0:
                break
            sport = _sport_for(d, slot_index)
            title = _title_for(d, label, sport)
            exists = session.scalar(
                select(Activity.id).where(Activity.title == title, Activity.is_demo.is_(True))
            )
            if exists is not None:
                continue  # idempotent: this (date, slot) already has a row
            _create_event(
                session,
                host,
                venue_pools,
                all_venues,
                club_by_sport,
                sport,
                title,
                start,
            )
            created += 1
            need -= 1
    if created:
        session.commit()
        logger.info("event refresh created %s upcoming activities", created)
    return created


def _prune(session: Session, cutoff: datetime) -> int:
    """Delete ONLY this module's generated events older than ``cutoff``."""
    stale_ids = list(
        session.scalars(
            select(Activity.id).where(
                Activity.is_demo.is_(True),
                Activity.title.like(f"{AUTO_TAG}%"),
                Activity.starts_at < cutoff,
            )
        ).all()
    )
    if not stale_ids:
        return 0
    session.execute(
        delete(ActivityParticipant).where(ActivityParticipant.activity_id.in_(stale_ids))
    )
    session.execute(delete(Activity).where(Activity.id.in_(stale_ids)))
    logger.info("event refresh pruned %s stale activities", len(stale_ids))
    return len(stale_ids)


def refresh_events(session: Session) -> dict[str, int]:
    """Prune stale generated rows then top up the upcoming window."""
    now = datetime.now(UTC)
    today = now.astimezone(JAKARTA).date()
    cutoff = datetime.combine(
        today - timedelta(days=PRUNE_AFTER_DAYS), time(0, 0), tzinfo=JAKARTA
    ).astimezone(UTC)
    pruned = _prune(session, cutoff)
    created = ensure_upcoming_events(session)
    # ``ensure_upcoming_events`` only commits when it inserted rows; commit here
    # too so a prune-only run (deletes) is never rolled back on session close.
    session.commit()
    return {"pruned": pruned, "created": created}
