"""Idempotent DEMO DATA seeder for RALLY (Indonesia localisation).

Creates clearly-labelled demo rows: activity categories, demo users, real
Indonesian venues with courts, named activities with participants and clubs.
Re-running is safe - every row is looked up by a natural key (slug / email /
name) and only created when missing. All rows carry is_demo=True.

Usage::

    DATABASE_URL=sqlite:///./rally_dev.db .venv/Scripts/python scripts/seed.py
"""
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "sqlite:///./rally_dev.db")

from sqlalchemy import create_engine, delete, func, select  # noqa: E402
from sqlalchemy.dialects.postgresql import UUID as PG_UUID  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# The demo seed intentionally builds one activity per LEGACY generic type
# (matched to the legacy venue catalog). The API itself now sources activity
# types from the SPORTS catalog (see app/core/activity_types.py shim); the
# LEGACY_* symbols are kept for exactly this demo-seed use.
from app.core.activity_types import (  # noqa: E402
    LEGACY_ACTIVITY_TYPE_BY_SLUG as ACTIVITY_TYPE_BY_SLUG,
    LEGACY_ACTIVITY_TYPES_PAYLOAD as ACTIVITY_TYPES_PAYLOAD,
)
from app.core.cities import CITY_PROVINCE  # noqa: E402
from app.core.venue_catalog import VENUE_BY_NAME, VENUE_ROWS  # noqa: E402
from app.core.sports import SPORT_BY_SLUG  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Base  # noqa: E402
from app.models.activity import (  # noqa: E402
    Activity,
    ActivityCategoryLink,
    ActivityParticipant,
)
from app.models.club import Club, ClubMember  # noqa: E402
from app.models.enums import (  # noqa: E402
    ActivityCategory,
    ActivityVisibility,
    ParticipantStatus,
    SkillLevel,
    TournamentFormat,
    TournamentStatus,
    UserRole,
)
from app.models.rating import LeaderboardEntry, MmrRating  # noqa: E402
from app.models.tournament import Tournament, TournamentEntry  # noqa: E402
from app.models.user import Profile, User  # noqa: E402
from app.models.venue import Venue, VenueAvailability, VenueCourt  # noqa: E402

DATABASE_URL = os.environ["DATABASE_URL"]

if DATABASE_URL.startswith("sqlite"):
    @compiles(PG_UUID, "sqlite")
    def _compile_uuid_sqlite(type_, compiler, **kw):
        return "CHAR(32)"

DEMO_PASSWORD = "RallyDemo123!"

# (slug, name, category, description, icon) - Bahasa Indonesia.
CATEGORIES = [
    ("sports", "Olahraga", ActivityCategory.SPORTS, "Olahraga tim dan raket", "trophy"),
    ("sports-football", "Sepak Bola & Futsal", ActivityCategory.SPORTS, "Futsal dan mini soccer", "futbol"),
    ("sports-basketball", "Basket", ActivityCategory.SPORTS, "Basket komunitas dan liga", "basketball"),
    ("sports-tennis", "Tenis", ActivityCategory.SPORTS, "Tunggal dan ganda", "table-tennis"),
    ("sports-badminton", "Bulu Tangkis", ActivityCategory.SPORTS, "Sewa lapangan dan sparring", "feather"),
    ("sports-billiard", "Biliar", ActivityCategory.SPORTS, "Biliar 8-ball dan 9-ball", "circle-dot"),
    ("sports-padel", "Padel", ActivityCategory.SPORTS, "Padel indoor dan outdoor", "racquet"),
    ("sports-volleyball", "Bola Voli", ActivityCategory.SPORTS, "Voli indoor dan pantai", "volleyball"),
    ("fitness", "Kebugaran", ActivityCategory.FITNESS, "Gym dan latihan kekuatan", "dumbbell"),
    ("fitness-gym", "Gym", ActivityCategory.FITNESS, "Latihan beban dan kardio", "activity"),
    ("fitness-running", "Lari", ActivityCategory.FITNESS, "Lari pagi dan lintasan", "footprints"),
    ("outdoor", "Alam Terbuka", ActivityCategory.OUTDOOR, "Hiking, sepeda, panjat", "mountain"),
    ("outdoor-hiking", "Hiking", ActivityCategory.OUTDOOR, "Pendakian sehari dan menginap", "boot"),
    ("outdoor-cycling", "Sepeda", ActivityCategory.OUTDOOR, "Rute jalan dan trail", "bike"),
    ("games", "Permainan", ActivityCategory.GAMES, "Papan, kartu, dan video", "dice"),
    ("games-board", "Board Games", ActivityCategory.GAMES, "Strategi dan pesta", "chess"),
    ("games-video", "Video Games", ActivityCategory.GAMES, "Konsol dan PC", "gamepad"),
    ("social", "Sosial", ActivityCategory.SOCIAL, "Kopdar dan kumpul komunitas", "users"),
    ("social-coffee", "Kopi Bareng", ActivityCategory.SOCIAL, "Ngopi santai", "coffee"),
    ("social-dining", "Makan Bareng", ActivityCategory.SOCIAL, "Makan kelompok", "utensils"),
    ("creative", "Kreatif", ActivityCategory.CREATIVE, "Seni, musik, menulis", "palette"),
    ("creative-music", "Jam Musik", ActivityCategory.CREATIVE, "Sesi jam terbuka", "music"),
    ("creative-art", "Seni & Sketsa", ActivityCategory.CREATIVE, "Life drawing dan sketsa", "brush"),
]


def _ensure_schema(engine):
    """Add newly-introduced venue columns on an existing SQLite DB.

    ``create_all`` never ALTERs existing tables, so a dev DB created before the
    province/area columns existed would fail. This is a no-op on Postgres.
    """
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(venues)")}
        if "province" not in cols:
            conn.exec_driver_sql("ALTER TABLE venues ADD COLUMN province VARCHAR(80)")
        if "area" not in cols:
            conn.exec_driver_sql("ALTER TABLE venues ADD COLUMN area VARCHAR(120)")
        if "venue_kind" not in cols:
            conn.exec_driver_sql("ALTER TABLE venues ADD COLUMN venue_kind VARCHAR(40)")
        if "sport_slugs" not in cols:
            conn.exec_driver_sql(
                "ALTER TABLE venues ADD COLUMN sport_slugs JSON DEFAULT '[]'"
            )
        court_cols = {
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(venue_courts)")
        }
        if "venue_kind" not in court_cols:
            conn.exec_driver_sql(
                "ALTER TABLE venue_courts ADD COLUMN venue_kind VARCHAR(40)"
            )
        if "resource_label" not in court_cols:
            conn.exec_driver_sql(
                "ALTER TABLE venue_courts ADD COLUMN resource_label VARCHAR(60)"
            )


def _seed_categories(db):
    created = 0
    for order, (slug, name, category, description, icon) in enumerate(CATEGORIES):
        if db.scalar(select(ActivityCategoryLink).where(ActivityCategoryLink.slug == slug)):
            continue
        db.add(ActivityCategoryLink(
            slug=slug, name=name, category=category, description=description,
            icon=icon, sort_order=order, is_active=True, is_demo=True))
        created += 1
    db.flush()
    return created


def _seed_users(db):
    specs = [
        ("admin@rally.id", "admin", UserRole.ADMIN, "Admin RALLY", "Jakarta"),
        ("host@rally.id", "host", UserRole.HOST, "Rizky Pratama", "Jakarta"),
        ("user@rally.id", "user", UserRole.USER, "Dewi Lestari", "Bandung"),
    ]
    users, created = {}, 0
    for email, username, role, display, city in specs:
        existing = db.scalar(select(User).where(User.email == email))
        if existing is None:
            existing = User(
                email=email, username=username,
                hashed_password=hash_password(DEMO_PASSWORD),
                role=role, is_active=True, is_verified=True, is_demo=True)
            existing.profile = Profile(
                display_name=display, city=city, country="ID",
                skill_level=SkillLevel.INTERMEDIATE, is_demo=True)
            db.add(existing)
            created += 1
        users[email] = existing
    db.flush()
    return users, created


# --- Venue catalog (venue<->activity-type matched) ------------------------
# Every venue is created for ONE activity type (see app/core/venue_catalog.py)
# and only ever hosts activities of that type, so e.g. a 'musik' activity can
# never be attached to a padel court. Location = city + province + area.
CATEGORY_OF_TYPE = {t["slug"]: t["category"] for t in ACTIVITY_TYPES_PAYLOAD}

#: Sports-catalog slugs (single source of truth for what may be seeded).
SPORTS_SLUGS = frozenset(SPORT_BY_SLUG)
#: Title template per activity type: legacy registry + sports catalog.
TITLE_BY_ATYPE = {slug: row["title"] for slug, row in ACTIVITY_TYPE_BY_SLUG.items()}
for _slug, _row in SPORT_BY_SLUG.items():
    TITLE_BY_ATYPE.setdefault(_slug, f"{_row['label_id']} di {{v}}")
del _slug, _row
#: Legacy generic slugs - PURGED, never seeded. RALLY is sports-only.
LEGACY_SLUGS = frozenset({
    "kopdar", "nobar", "boardgame", "esport", "musik", "seni", "sketsa",
})

# Court surface + hourly price (IDR) per activity type - demo, plausible.
COURT_SPEC = {
    "padel": ("artificial", 200000), "badminton": ("kayu", 80000),
    "basket": ("parket", 90000), "billiard": ("kain", 60000),
    "futsal": ("sintetis", 150000), "tenis": ("keras", 140000),
    "renang": ("kolam", 50000), "lari": ("lintasan", 0),
    "gym": ("lantai", 50000), "yoga": ("lantai", 60000),
    "sepeda": ("jalan", 0), "hiking": ("tanah", 0), "gowes": ("jalan", 0),
    "panjat": ("dinding", 90000), "camping": ("tanah", 0),
    "boardgame": ("meja", 40000), "esport": ("pc", 30000),
    "kopdar": ("meja", 0), "nobar": ("meja", 0),
    "musik": ("studio", 70000), "seni": ("studio", 60000),
    "sketsa": ("studio", 50000),
}


def _venue_specs():
    """Expand VENUE_ROWS into full venue specs with province, area + sport types."""
    specs = []
    for city, area, atype, name in VENUE_ROWS:
        province = CITY_PROVINCE.get(city)
        category = ActivityCategory(CATEGORY_OF_TYPE.get(atype, "sports"))
        surface, price = COURT_SPEC.get(atype, ("mat", 75000))
        # Sport-awareness: the catalog venue carries the venue_kind, the typed
        # resources and the sport slugs this venue serves.
        catalog = VENUE_BY_NAME.get(name)
        sport_slugs = list(catalog.sport_slugs) if catalog is not None else []
        venue_kind = catalog.venue_kind if catalog is not None else None
        resource_label = None
        if catalog is not None and catalog.resources:
            resource_label = catalog.resources[0].label
        specs.append((name, category, atype, f"Kawasan {area}, {city}",
                      city, province, area, surface, price,
                      venue_kind, resource_label, sport_slugs))
    return specs


VENUE_SPECS = _venue_specs()


def _reset_demo_catalog(db):
    """Remove stale demo activities/venues that are no longer in the catalog.

    The seed is additive by design, so older demo rows (e.g. venues in a city
    no longer in the catalog, or non-IDR rows) would otherwise survive. We only
    ever delete rows flagged is_demo=True - real user data is untouched.
    """
    from app.models.activity import ActivityRecurrence
    from app.models.booking import Booking
    from app.models.match import Match
    from app.models.social import ChatRoom, CheckIn

    keep_venues = {name for _c, _a, _t, name in VENUE_ROWS}
    keep_titles = {
        TITLE_BY_ATYPE[atype].format(v=name)
        for _c, _a, atype, name in VENUE_ROWS
    }
    stale_venues = [
        v.id for v in db.scalars(select(Venue).where(Venue.is_demo.is_(True)))
        if v.name not in keep_venues
    ]
    stale_acts = [
        a.id for a in db.scalars(select(Activity).where(Activity.is_demo.is_(True)))
        if a.title not in keep_titles
    ]

    removed = 0
    if stale_acts:
        db.execute(delete(ActivityParticipant).where(
            ActivityParticipant.activity_id.in_(stale_acts)))
        db.execute(delete(ActivityRecurrence).where(
            ActivityRecurrence.activity_id.in_(stale_acts)))
        db.execute(delete(ChatRoom).where(ChatRoom.activity_id.in_(stale_acts)))
        db.execute(delete(CheckIn).where(CheckIn.activity_id.in_(stale_acts)))
        db.execute(delete(Booking).where(Booking.activity_id.in_(stale_acts)))
        db.execute(delete(Match).where(Match.activity_id.in_(stale_acts)))
        removed = db.execute(delete(Activity).where(
            Activity.id.in_(stale_acts))).rowcount or 0
    if stale_venues:
        db.execute(delete(VenueCourt).where(VenueCourt.venue_id.in_(stale_venues)))
        db.execute(delete(Tournament).where(Tournament.venue_id.in_(stale_venues)))
        db.execute(delete(Venue).where(Venue.id.in_(stale_venues)))
    db.flush()
    return removed


def _seed_venues(db, owner):
    venues, created = [], 0
    for (name, category, atype, address, city, province, area,
         surface, price, venue_kind, resource_label, sport_slugs) in VENUE_SPECS:
        existing = db.scalar(select(Venue).where(Venue.name == name))
        if existing is None:
            existing = Venue(
                owner_id=owner.id, name=name, description=f"DEMO DATA venue: {name}",
                address_line=address, city=city, province=province, area=area,
                country="ID", category=category, timezone="Asia/Jakarta",
                is_active=True, is_demo=True,
                venue_kind=venue_kind, sport_slugs=sport_slugs)
            db.add(existing)
            db.flush()
            # One typed resource per demo venue (venue_kind + resource_label).
            court = VenueCourt(
                venue_id=existing.id, name=f"Area {atype.title()}",
                surface=surface, capacity=8, hourly_price_cents=price,
                is_active=True, venue_kind=venue_kind, resource_label=resource_label)
            db.add(court)
            db.flush()
            # Availability is generated PER RESOURCE (this court).
            for weekday in range(7):
                db.add(VenueAvailability(
                    court_id=court.id, weekday=weekday,
                    opens_at=time(6, 0), closes_at=time(22, 0), is_active=True))
            created += 1
        else:
            # Backfill location fields on venues created before these columns.
            existing.city = city
            existing.province = province
            existing.area = area
            existing.address_line = address
            # Keep the primary category in sync with the catalog type.
            existing.category = category
            # Backfill sport-awareness on venues created before these columns.
            existing.venue_kind = venue_kind
            existing.sport_slugs = sport_slugs
            for court in db.scalars(
                select(VenueCourt).where(VenueCourt.venue_id == existing.id)
            ):
                court.venue_kind = venue_kind
                court.resource_label = resource_label
        venues.append(existing)
    db.flush()
    return venues, created


def _seed_clubs(db, host, user):
    specs = [
        ("jakarta-runners", "Jakarta Runners", ActivityCategory.FITNESS, "Jakarta"),
        ("bandung-hoops", "Bandung Hoops", ActivityCategory.SPORTS, "Bandung"),
        ("padel-kemang-community", "Padel Kemang Community", ActivityCategory.SPORTS, "Jakarta"),
    ]
    clubs, created = [], 0
    for slug, name, category, city in specs:
        existing = db.scalar(select(Club).where(Club.slug == slug))
        if existing is None:
            existing = Club(
                owner_id=host.id, slug=slug, name=name,
                description=f"DEMO DATA club: {name}", category=category,
                city=city, is_public=True, is_demo=True)
            db.add(existing)
            db.flush()
            db.add(ClubMember(club_id=existing.id, user_id=host.id,
                              role=UserRole.CLUB_ORGANIZER, is_active=True,
                              joined_at=datetime.now(UTC)))
            db.add(ClubMember(club_id=existing.id, user_id=user.id,
                              role=UserRole.USER, is_active=True,
                              joined_at=datetime.now(UTC)))
            created += 1
        clubs.append(existing)
    db.flush()
    return clubs, created


# Real named Indonesian activities. The TITLE is the VENUE / LOCATION name
# (never a district or region). Region lives only on the venue city.
# Activity content per type: (skill, capacity, cost_idr, description). One
# activity is generated PER VENUE so the catalog spans every city; the venue
# determines the activity type (venue<->type match is enforced by construction).
ACTIVITY_CONTENT = {
    "padel": (SkillLevel.INTERMEDIATE, 4, 150000,
              "Main padel bareng di {v}. Sudah termasuk sewa lapangan dan bola."),
    "badminton": (SkillLevel.INTERMEDIATE, 8, 50000,
                  "Sparring bulu tangkis di {v}. Dua lapangan, ganda campuran."),
    "basket": (SkillLevel.ANY, 10, 45000,
               "Basket pickup di {v}. Full court, tim dibagi di lokasi."),
    "billiard": (SkillLevel.ADVANCED, 16, 75000,
                 "Turnamen 8-ball di {v}. Hadiah untuk juara 1-3."),
    "futsal": (SkillLevel.ANY, 12, 65000,
               "Futsal santai di {v}. Daftar cepat, kuota terbatas."),
    "tenis": (SkillLevel.INTERMEDIATE, 4, 100000,
              "Tenis ganda di {v}. Sudah termasuk sewa lapangan."),
    "renang": (SkillLevel.BEGINNER, 10, 50000,
               "Renang bareng di {v}. Cocok untuk semua level."),
    "lari": (SkillLevel.ANY, 20, 0,
             "Lari pagi 5K di {v}. Gratis, kumpul jam 6 pagi."),
    "gym": (SkillLevel.BEGINNER, 8, 0,
            "Sesi gym bareng di {v}. Ada coach pembimbing. Gratis."),
    "yoga": (SkillLevel.BEGINNER, 15, 0,
             "Yoga pagi untuk pemula di {v}. Bawa matras sendiri."),
    "sepeda": (SkillLevel.ANY, 15, 0,
               "Gowes santai di {v}. Rute ramah pemula, gratis."),
    "hiking": (SkillLevel.INTERMEDIATE, 12, 50000,
               "Hiking seru di {v}. Bawa air dan jaket."),
    "gowes": (SkillLevel.ANY, 15, 0,
              "Gowes bareng komunitas di {v}. Gratis, semua level."),
    "panjat": (SkillLevel.INTERMEDIATE, 8, 90000,
               "Latihan panjat tebing di {v}. Alat tersedia."),
    "camping": (SkillLevel.ANY, 20, 0,
                "Camping bareng di {v}. Bawa tenda dan sleeping bag."),
    "boardgame": (SkillLevel.ANY, 8, 40000,
                  "Board game night di {v}. Bawa board game favoritmu."),
    "esport": (SkillLevel.ANY, 16, 30000,
               "Turnamen e-sport di {v}. Hadiah untuk juara."),
    "kopdar": (SkillLevel.ANY, 12, 0,
               "Kopdar santai di {v}. Gratis, ngopi bareng komunitas."),
    "nobar": (SkillLevel.ANY, 20, 0,
              "Nobar bareng di {v}. Gratis, datang lebih awal."),
    "musik": (SkillLevel.INTERMEDIATE, 6, 70000,
              "Jam musik bareng di {v}. Bawa alat sendiri bila ada."),
    "seni": (SkillLevel.BEGINNER, 10, 60000,
             "Kelas seni untuk pemula di {v}. Alat sudah disiapkan."),
    "sketsa": (SkillLevel.BEGINNER, 10, 50000,
               "Sketsa bareng di {v}. Bawa buku gambar sendiri."),
}


def _seed_activities(db, host, user, admin, venues):
    """Create one activity per venue; the venue's type drives the activity."""
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    created = participants = 0
    for i, (city, area, atype, name) in enumerate(VENUE_ROWS):
        # Sports-only: never seed legacy generic types (kopdar/nobar/esport/...).
        if atype in LEGACY_SLUGS:
            continue
        venue = db.scalar(select(Venue).where(Venue.name == name))
        if venue is None:
            continue
        skill, capacity, cost_idr, desc_t = ACTIVITY_CONTENT.get(atype, (SkillLevel.ANY, 12, 75000, "Latihan {v}."))
        title = TITLE_BY_ATYPE[atype].format(v=venue.name)
        # Spread start times across the next ~7 days, varied by hour.
        starts_at = now + timedelta(days=(i % 7), hours=(i % 12) + 1)
        existing = db.scalar(select(Activity).where(Activity.title == title))
        if existing is not None:
            # Idempotent re-run: keep the demo window fresh (next ~7 days).
            existing.starts_at = starts_at
            existing.ends_at = starts_at + timedelta(hours=2)
            continue
        activity = Activity(
            host_id=host.id, venue_id=venue.id, title=title,
            description=desc_t.format(v=venue.name),
            category=ActivityCategory(CATEGORY_OF_TYPE.get(atype, "sports")),
            activity_type=atype, skill_level=skill,
            sport_slug=atype if atype in SPORTS_SLUGS else None,
            sport_category=(SPORT_BY_SLUG[atype]["category"]
                            if atype in SPORTS_SLUGS else None),
            visibility=ActivityVisibility.PUBLIC,
            starts_at=starts_at, ends_at=starts_at + timedelta(hours=2),
            max_participants=capacity, cost_per_person_cents=cost_idr,
            currency="IDR", is_demo=True)
        db.add(activity)
        db.flush()
        db.add(ActivityParticipant(activity_id=activity.id, user_id=host.id,
                                   status=ParticipantStatus.CONFIRMED, is_host=True,
                                   joined_at=datetime.now(UTC)))
        db.add(ActivityParticipant(activity_id=activity.id, user_id=user.id,
                                   status=ParticipantStatus.CONFIRMED, is_host=False,
                                   joined_at=datetime.now(UTC)))
        participants += 2
        if created % 2 == 0:
            db.add(ActivityParticipant(activity_id=activity.id, user_id=admin.id,
                                       status=ParticipantStatus.REQUESTED, is_host=False,
                                       joined_at=datetime.now(UTC)))
            participants += 1
        created += 1
    db.flush()
    return created, participants


# Demo MMR: (email, category, rating, games, wins, losses, draws).
RATING_SPECS = [
    ("host@rally.id", "sports", 1487, 42, 27, 12, 3),
    ("host@rally.id", "fitness", 1332, 18, 11, 6, 1),
    ("host@rally.id", "outdoor", 1265, 9, 5, 3, 1),
    ("user@rally.id", "sports", 1398, 31, 18, 11, 2),
    ("user@rally.id", "fitness", 1441, 25, 16, 7, 2),
    ("user@rally.id", "games", 1210, 12, 6, 6, 0),
    ("admin@rally.id", "sports", 1156, 7, 3, 4, 0),
    ("admin@rally.id", "creative", 1240, 5, 3, 1, 1),
]


def _seed_ratings(db, users):
    """Per-category MMR so leaderboards, profiles and the home MMR panel are live."""
    created = 0
    for email, category, rating, games, wins, losses, draws in RATING_SPECS:
        user = users[email]
        # Legacy demo rows are sport-less: scope them by category so each
        # (user, category) pair stays distinct under the per-sport unique key.
        scope = f"category:{category}"
        existing = db.scalar(
            select(MmrRating).where(
                MmrRating.user_id == user.id, MmrRating.sport_slug == scope
            )
        )
        if existing is None:
            db.add(
                MmrRating(
                    user_id=user.id, category=category, sport_slug=scope, rating=rating,
                    games_played=games, wins=wins, losses=losses, draws=draws,
                )
            )
            created += 1
    db.flush()
    return created


# Demo tournaments. (slug, name, category, format, status, max_entries, fee, day_offset)
TOURNAMENT_SPECS = [
    ("padel-open-jakarta", "Padel Open Jakarta 2026", ActivityCategory.SPORTS,
     TournamentFormat.SINGLE_ELIMINATION, TournamentStatus.OPEN, 16, 250000, 12),
    ("billiard-8ball-tebet", "Turnamen Billiard 8-Ball Tebet", ActivityCategory.SPORTS,
     TournamentFormat.SINGLE_ELIMINATION, TournamentStatus.OPEN, 32, 100000, 18),
    ("futsal-league-bsd", "Liga Futsal BSD", ActivityCategory.SPORTS,
     TournamentFormat.ROUND_ROBIN, TournamentStatus.OPEN, 12, 500000, 21),
]


def _seed_tournaments(db, users, venues):
    created = 0
    organizer = users["host@rally.id"]
    for slug, name, category, fmt, status, max_entries, fee, day_offset in TOURNAMENT_SPECS:
        existing = db.scalar(select(Tournament).where(Tournament.slug == slug))
        if existing is not None:
            continue
        starts_at = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
        tournament = Tournament(
            organizer_id=organizer.id, slug=slug, name=name,
            description=f"{name} - turnamen resmi RALLY untuk komunitas Indonesia.",
            category=category, format=fmt, status=status,
            max_entries=max_entries, entry_fee_cents=fee, currency="IDR",
            starts_at=starts_at, ends_at=starts_at + timedelta(days=1), is_demo=True,
        )
        db.add(tournament)
        db.flush()
        db.add(TournamentEntry(tournament_id=tournament.id, user_id=organizer.id))
        db.add(TournamentEntry(tournament_id=tournament.id, user_id=users["user@rally.id"].id))
        created += 1
    db.flush()
    return created



def _purge_legacy_activities(db) -> int:
    """Delete legacy-typed (non-sports) activity rows + their participants.

    RALLY is sports-only; legacy generic demo rows (kopdar/nobar/esport/musik/
    seni/sketsa/boardgame) must never survive a reseed.
    """
    from sqlalchemy import delete as _delete
    legacy = tuple(sorted(LEGACY_SLUGS))
    if not legacy:
        return 0
    rows = db.scalars(
        select(Activity.id).where(Activity.activity_type.in_(legacy))
    ).all()
    if not rows:
        return 0
    db.execute(_delete(ActivityParticipant).where(
        ActivityParticipant.activity_id.in_(rows)))
    db.execute(_delete(Activity).where(Activity.id.in_(rows)))
    db.flush()
    return len(rows)

def main():
    engine = create_engine(DATABASE_URL, future=True)
    Base.metadata.create_all(engine)
    _ensure_schema(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as db:
        cat_created = _seed_categories(db)
        users, user_created = _seed_users(db)
        removed = _reset_demo_catalog(db)
        venues, venue_created = _seed_venues(db, users["host@rally.id"])
        _purge_legacy_activities(db)
        clubs, club_created = _seed_clubs(db, users["host@rally.id"], users["user@rally.id"])
        act_created, part_created = _seed_activities(
            db, users["host@rally.id"], users["user@rally.id"],
            users["admin@rally.id"], venues)
        rating_created = _seed_ratings(db, users)
        tour_created = _seed_tournaments(db, users, venues)
        db.commit()
        n_cat = db.scalar(select(func.count()).select_from(ActivityCategoryLink))
        n_ven = db.scalar(select(func.count()).select_from(Venue))
        n_club = db.scalar(select(func.count()).select_from(Club))
        n_act = db.scalar(select(func.count()).select_from(Activity))
        n_usr = db.scalar(select(func.count()).select_from(User))
        n_court = db.scalar(select(func.count()).select_from(VenueCourt))
        n_part = db.scalar(select(func.count()).select_from(ActivityParticipant))
        n_rating = db.scalar(select(func.count()).select_from(MmrRating))
        n_tour = db.scalar(select(func.count()).select_from(Tournament))

    print("RALLY seed complete (DEMO DATA, is_demo=True).")
    print(f"  database:            {DATABASE_URL}")
    print(f"  activity categories: {cat_created} created (total {n_cat})")
    print(f"  users:               {user_created} created (total {n_usr}) "
          f"[admin@rally.id / host@rally.id / user@rally.id, password {DEMO_PASSWORD}]")
    print(f"  stale demo rows:     {removed} removed before reseed")
    print(f"  venues:              {venue_created} created (total {n_ven}, {n_court} courts)")
    print(f"  clubs:               {club_created} created (total {n_club})")
    print(f"  activities:          {act_created} created (total {n_act}) "
          f"with {part_created} participant rows (total {n_part})")
    print(f"  mmr ratings:         {rating_created} created (total {n_rating})")
    print(f"  tournaments:         {tour_created} created (total {n_tour})")
    print("Seed is idempotent: re-running creates nothing new.")


if __name__ == "__main__":
    main()
