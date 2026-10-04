"""RALLY SPORTS CATALOG - single source of truth for sports.

Extensible and data-driven: adding a sport never requires touching application
code. Each sport declares its category, the venue kind and resource label used
by the booking engine, whether it is competitive (MMR-bearing), plus its
variants, formats and metrics.

Row shape: (slug, label_id, label_en, category, venue_kind, resource_label,
competitive, variants, formats, metrics) where the last three are
comma-separated (empty string = none).
"""
from __future__ import annotations

#: (slug, label_id, label_en, blurb)
SPORT_CATEGORIES: list[tuple[str, str, str, str]] = [
    ("racket", "Raket", "Racket", "Padel, tenis, bulu tangkis, squash"),
    ("team", "Bola & Tim", "Team", "Sepak bola, basket, voli, futsal"),
    ("combat", "Bela Diri", "Combat", "Tinju, BJJ, judo, MMA, karate"),
    ("strength", "Kekuatan", "Strength", "Angkat besi, powerlifting, crossfit"),
    ("running", "Atletik & Lari", "Athletics & Running", "Lari, maraton, atletik"),
    ("cycling", "Sepeda", "Cycling", "Sepeda jalan, gunung, BMX"),
    ("water", "Air", "Water", "Renang, selancar, dayung, polo air"),
    ("winter", "Es & Salju", "Winter & Ice", "Hoki es, ski, seluncur"),
    ("precision", "Presisi", "Precision", "Golf, biliar, panahan, catur"),
    ("gymnastics", "Senam", "Gymnastics", "Senam artistik, ritmik, trampolin"),
    ("outdoor", "Panjat & Alam", "Climbing & Outdoor", "Panjat, bouldering, hiking"),
    ("other", "Lainnya", "Other", "Olahraga lain yang diakui"),
]

_S: list[tuple[str, str, str, str, str, str, bool, str, str, str]] = [
    # ---------------- RACKET ----------------
    ("padel", "Padel", "Padel", "racket", "court", "Court", True, "singles,doubles", "ranked,casual", "mmr,wins,losses,win_rate,form"),
    ("tennis", "Tenis", "Tennis", "racket", "court", "Court", True, "singles,doubles,mixed_doubles", "ranked,casual", "mmr,wins,losses,win_rate,form"),
    ("badminton", "Bulu Tangkis", "Badminton", "racket", "court", "Court", True, "singles,doubles,mixed_doubles", "ranked,casual", "mmr,wins,losses,win_rate,form"),
    ("table-tennis", "Tenis Meja", "Table Tennis", "racket", "hall", "Table", True, "singles,doubles", "ranked,casual", "mmr,wins,losses,win_rate"),
    ("squash", "Squash", "Squash", "racket", "court", "Court", True, "singles,doubles", "ranked,casual", "mmr,wins,losses"),
    ("pickleball", "Pickleball", "Pickleball", "racket", "court", "Court", True, "singles,doubles,mixed_doubles", "ranked,casual", "mmr,wins,losses"),
    ("racquetball", "Racquetball", "Racquetball", "racket", "court", "Court", True, "singles,doubles", "ranked,casual", "mmr,wins,losses"),
    ("beach-tennis", "Tenis Pantai", "Beach Tennis", "racket", "court", "Court", True, "singles,doubles", "ranked,casual", "mmr,wins,losses"),
    # ---------------- TEAM ----------------
    ("football", "Sepak Bola", "Football", "team", "field", "Field", True, "5v5,7v7,9v9,11v11", "ranked,casual", "mmr,wins,losses,goals,assists,form"),
    ("futsal", "Futsal", "Futsal", "team", "field", "Field", True, "4v4,5v5", "ranked,casual", "mmr,wins,losses,goals,assists"),
    ("basketball", "Basket", "Basketball", "team", "court", "Court", True, "5x5", "ranked,casual", "mmr,wins,losses,points,assists"),
    ("basketball-3x3", "Basket 3x3", "3x3 Basketball", "team", "court", "Court", True, "3x3", "ranked,casual", "mmr,wins,losses,points"),
    ("volleyball", "Bola Voli", "Volleyball", "team", "court", "Court", True, "6v6", "ranked,casual", "mmr,wins,losses,sets"),
    ("beach-volleyball", "Voli Pantai", "Beach Volleyball", "team", "court", "Court", True, "2v2", "ranked,casual", "mmr,wins,losses,sets"),
    ("handball", "Bola Tangan", "Handball", "team", "court", "Court", True, "7v7", "ranked,casual", "mmr,wins,losses,goals"),
    ("rugby", "Rugby", "Rugby", "team", "field", "Field", True, "15v15", "ranked,casual", "mmr,wins,losses,points"),
    ("rugby-sevens", "Rugby Sevens", "Rugby Sevens", "team", "field", "Field", True, "7v7", "ranked,casual", "mmr,wins,losses,points"),
    ("american-football", "Sepak Bola Amerika", "American Football", "team", "field", "Field", True, "11v11,flag", "ranked,casual", "mmr,wins,losses,points"),
    ("baseball", "Bisbol", "Baseball", "team", "field", "Field", True, "9v9", "ranked,casual", "mmr,wins,losses,runs"),
    ("softball", "Sofbol", "Softball", "team", "field", "Field", True, "9v9", "ranked,casual", "mmr,wins,losses,runs"),
    ("cricket", "Kriket", "Cricket", "team", "field", "Field", True, "T20,ODI,Test", "ranked,casual", "mmr,wins,losses,runs"),
    ("hockey", "Hoki", "Hockey", "team", "field", "Field", True, "11v11", "ranked,casual", "mmr,wins,losses,goals"),
    ("field-hockey", "Hoki Lapangan", "Field Hockey", "team", "field", "Field", True, "11v11", "ranked,casual", "mmr,wins,losses,goals"),
    ("floorball", "Floorball", "Floorball", "team", "court", "Court", True, "5v5,6v6", "ranked,casual", "mmr,wins,losses,goals"),
    ("netball", "Netball", "Netball", "team", "court", "Court", True, "7v7", "ranked,casual", "mmr,wins,losses,goals"),
    ("ultimate-frisbee", "Ultimate Frisbee", "Ultimate Frisbee", "team", "field", "Field", True, "5v5,7v7", "ranked,casual", "mmr,wins,losses,points"),
    ("lacrosse", "Lakros", "Lacrosse", "team", "field", "Field", True, "10v10", "ranked,casual", "mmr,wins,losses,goals"),
    ("dodgeball", "Dodgeball", "Dodgeball", "team", "court", "Court", True, "6v6", "ranked,casual", "mmr,wins,losses"),
    ("kabaddi", "Kabaddi", "Kabaddi", "team", "court", "Court", True, "7v7", "ranked,casual", "mmr,wins,losses"),
    # ---------------- COMBAT ----------------
    ("boxing", "Tinju", "Boxing", "combat", "ring", "Ring", True, "training,sparring,competitive", "ranked,casual", "mmr,wins,losses,weight_class,sessions"),
    ("kickboxing", "Kickboxing", "Kickboxing", "combat", "ring", "Ring", True, "training,sparring,competitive", "ranked,casual", "mmr,wins,losses,weight_class"),
    ("muay-thai", "Muay Thai", "Muay Thai", "combat", "ring", "Ring", True, "training,sparring,competitive", "ranked,casual", "mmr,wins,losses,weight_class"),
    ("mma", "MMA", "MMA", "combat", "cage", "Cage", True, "training,sparring,competitive", "ranked,casual", "mmr,wins,losses,weight_class"),
    ("bjj", "Brazilian Jiu-Jitsu", "Brazilian Jiu-Jitsu", "combat", "mat", "Mat Area", True, "gi,no-gi,open-mat,competition", "ranked,casual", "mmr,wins,losses,belt"),
    ("judo", "Judo", "Judo", "combat", "mat", "Mat Area", True, "training,randori,competition", "ranked,casual", "mmr,wins,losses,belt"),
    ("karate", "Karate", "Karate", "combat", "dojo", "Mat Area", True, "kata,kumite,training", "ranked,casual", "mmr,wins,losses,belt"),
    ("taekwondo", "Taekwondo", "Taekwondo", "combat", "dojo", "Mat Area", True, "poomsae,kyorugi,training", "ranked,casual", "mmr,wins,losses,belt"),
    ("wrestling", "Gulat", "Wrestling", "combat", "mat", "Mat Area", True, "freestyle,greco-roman", "ranked,casual", "mmr,wins,losses,weight_class"),
    ("sambo", "Sambo", "Sambo", "combat", "mat", "Mat Area", True, "sport,combat", "ranked,casual", "mmr,wins,losses,weight_class"),
    ("sanda", "Sanda", "Sanda", "combat", "ring", "Ring", True, "training,sparring,competitive", "ranked,casual", "mmr,wins,losses,weight_class"),
    ("wushu", "Wushu", "Wushu", "combat", "dojo", "Mat Area", True, "taolu,sanda", "ranked,casual", "mmr,wins,losses"),
    ("aikido", "Aikido", "Aikido", "combat", "dojo", "Mat Area", False, "training", "casual", "sessions"),
    ("kendo", "Kendo", "Kendo", "combat", "dojo", "Mat Area", True, "training,shiai", "ranked,casual", "mmr,wins,losses,rank"),
    ("fencing", "Anggar", "Fencing", "combat", "hall", "Piste", True, "foil,epee,sabre", "ranked,casual", "mmr,wins,losses"),
    ("savate", "Savate", "Savate", "combat", "ring", "Ring", True, "training,sparring,competitive", "ranked,casual", "mmr,wins,losses"),
    ("krav-maga", "Krav Maga", "Krav Maga", "combat", "dojo", "Mat Area", False, "training", "casual", "sessions"),
    ("pencak-silat", "Pencak Silat", "Pencak Silat", "combat", "mat", "Mat Area", True, "tanding,seni", "ranked,casual", "mmr,wins,losses"),
    ("tarung-derajat", "Tarung Derajat", "Tarung Derajat", "combat", "mat", "Mat Area", True, "tanding", "ranked,casual", "mmr,wins,losses"),
    # ---------------- STRENGTH ----------------
    ("weightlifting", "Angkat Besi", "Weightlifting", "strength", "gym", "Platform", True, "snatch,clean_and_jerk,total", "ranked,casual", "mmr,total_kg,bodyweight"),
    ("powerlifting", "Powerlifting", "Powerlifting", "strength", "gym", "Platform", True, "squat,bench,deadlift,total", "ranked,casual", "mmr,total_kg,bodyweight"),
    ("bodybuilding", "Binaraga", "Bodybuilding", "strength", "gym", "Training Area", True, "classic,open", "ranked,casual", "placement"),
    ("crossfit", "CrossFit", "CrossFit", "strength", "gym", "Training Area", True, "wod,competition", "ranked,casual", "mmr,points"),
    ("strongman", "Strongman", "Strongman", "strength", "gym", "Training Area", True, "competition", "ranked,casual", "mmr,points"),
    ("calisthenics", "Calisthenics", "Calisthenics", "strength", "gym", "Training Area", False, "training", "casual", "sessions"),
    # ---------------- RUNNING / ATHLETICS ----------------
    ("running", "Lari", "Running", "running", "track", "Lane", True, "5k,10k,fun_run", "ranked,casual", "mmr,time_pb,distance"),
    ("sprinting", "Lari Cepat", "Sprinting", "running", "track", "Lane", True, "100m,200m,400m", "ranked,casual", "mmr,time_pb"),
    ("marathon", "Maraton", "Marathon", "running", "route", "Route", True, "42k", "ranked,casual", "mmr,time_pb"),
    ("half-marathon", "Half Marathon", "Half Marathon", "running", "route", "Route", True, "21k", "ranked,casual", "mmr,time_pb"),
    ("trail-running", "Trail Running", "Trail Running", "running", "trail", "Route", True, "trail", "ranked,casual", "mmr,time_pb,distance"),
    ("track-field", "Atletik", "Track & Field", "running", "track", "Lane", True, "sprint,distance,relay", "ranked,casual", "mmr,time_pb"),
    ("long-jump", "Lompat Jauh", "Long Jump", "running", "track", "Pit", True, "standing,running", "ranked,casual", "mmr,distance_pb"),
    ("high-jump", "Lompat Tinggi", "High Jump", "running", "track", "Pit", True, "scissors,fosbury", "ranked,casual", "mmr,height_pb"),
    ("pole-vault", "Lompat Galah", "Pole Vault", "running", "track", "Pit", True, "standard", "ranked,casual", "mmr,height_pb"),
    ("shot-put", "Tolak Peluru", "Shot Put", "running", "field", "Circle", True, "standard", "ranked,casual", "mmr,distance_pb"),
    ("discus", "Lempar Cakram", "Discus", "running", "field", "Circle", True, "standard", "ranked,casual", "mmr,distance_pb"),
    ("javelin", "Lempar Lembing", "Javelin", "running", "field", "Runway", True, "standard", "ranked,casual", "mmr,distance_pb"),
    # ---------------- CYCLING ----------------
    ("road-cycling", "Sepeda Jalan", "Road Cycling", "cycling", "route", "Route", True, "road", "ranked,casual", "mmr,distance,time_pb"),
    ("mountain-biking", "Sepeda Gunung", "Mountain Biking", "cycling", "trail", "Trail", True, "xc,downhill,enduro", "ranked,casual", "mmr,distance,time_pb"),
    ("bmx", "BMX", "BMX", "cycling", "track", "Track", True, "race,freestyle", "ranked,casual", "mmr,time_pb"),
    ("track-cycling", "Sepeda Trek", "Track Cycling", "cycling", "velodrome", "Track", True, "sprint,pursuit", "ranked,casual", "mmr,time_pb"),
    ("gravel-cycling", "Sepeda Gravel", "Gravel Cycling", "cycling", "route", "Route", True, "gravel", "ranked,casual", "mmr,distance,time_pb"),
    # ---------------- WATER ----------------
    ("swimming", "Renang", "Swimming", "water", "pool", "Lane", True, "freestyle,backstroke,breaststroke,butterfly,medley", "ranked,casual", "mmr,time_pb,distance"),
    ("diving", "Loncat Indah", "Diving", "water", "pool", "Platform", True, "1m,3m,10m", "ranked,casual", "mmr,score"),
    ("open-water-swimming", "Renang Perairan Terbuka", "Open Water Swimming", "water", "openwater", "Route", True, "5k,10k", "ranked,casual", "mmr,time_pb,distance"),
    ("surfing", "Selancar", "Surfing", "water", "beach", "Break", True, "shortboard,longboard", "ranked,casual", "mmr,score"),
    ("windsurfing", "Windsurfing", "Windsurfing", "water", "beach", "Launch", True, "slalom,wave", "ranked,casual", "mmr,score"),
    ("sailing", "Berlayar", "Sailing", "water", "marina", "Berth", True, "dinghy,keelboat", "ranked,casual", "mmr,placement"),
    ("kayaking", "Kayak", "Kayaking", "water", "river", "Launch", True, "sprint,slalom", "ranked,casual", "mmr,time_pb"),
    ("canoeing", "Kano", "Canoeing", "water", "river", "Launch", True, "sprint,slalom", "ranked,casual", "mmr,time_pb"),
    ("rowing", "Dayung", "Rowing", "water", "river", "Lane", True, "single,double,eight", "ranked,casual", "mmr,time_pb"),
    ("rafting", "Arung Jeram", "Rafting", "water", "river", "Launch", False, "group", "casual", "sessions"),
    ("water-polo", "Polo Air", "Water Polo", "water", "pool", "Pool", True, "7v7", "ranked,casual", "mmr,wins,losses,goals"),
    # ---------------- WINTER ----------------
    ("ice-hockey", "Hoki Es", "Ice Hockey", "winter", "rink", "Rink", True, "5v5", "ranked,casual", "mmr,wins,losses,goals"),
    ("figure-skating", "Seluncur Indah", "Figure Skating", "winter", "rink", "Rink", True, "singles,pairs,ice_dance", "ranked,casual", "mmr,score"),
    ("speed-skating", "Seluncur Cepat", "Speed Skating", "winter", "rink", "Lane", True, "500m,1000m,1500m", "ranked,casual", "mmr,time_pb"),
    ("short-track", "Short Track", "Short Track", "winter", "rink", "Lane", True, "500m,1000m,1500m", "ranked,casual", "mmr,time_pb"),
    ("curling", "Curling", "Curling", "winter", "rink", "Sheet", True, "team", "ranked,casual", "mmr,wins,losses"),
    ("skiing", "Ski", "Skiing", "winter", "slope", "Run", True, "alpine,nordic,freestyle", "ranked,casual", "mmr,time_pb"),
    ("snowboarding", "Snowboard", "Snowboarding", "winter", "slope", "Run", True, "slopestyle,halfpipe,boardercross", "ranked,casual", "mmr,score"),
    # ---------------- PRECISION ----------------
    ("golf", "Golf", "Golf", "precision", "course", "Hole", True, "stroke_play,match_play", "ranked,casual", "mmr,handicap,score"),
    ("bowling", "Boling", "Bowling", "precision", "lane", "Lane", True, "singles,team", "ranked,casual", "mmr,score"),
    ("billiards", "Biliar", "Billiards", "precision", "hall", "Table", True, "8-ball,9-ball,10-ball", "ranked,casual", "mmr,wins,losses"),
    ("pool", "Pool", "Pool", "precision", "hall", "Table", True, "8-ball,9-ball,10-ball", "ranked,casual", "mmr,wins,losses"),
    ("snooker", "Snooker", "Snooker", "precision", "hall", "Table", True, "frame", "ranked,casual", "mmr,wins,losses,break"),
    ("darts", "Panah Sasar", "Darts", "precision", "lane", "Board", True, "501,cricket", "ranked,casual", "mmr,score"),
    ("archery", "Panahan", "Archery", "precision", "range", "Range", True, "recurve,compound,barebow", "ranked,casual", "mmr,score"),
    ("shooting", "Menembak", "Shooting Sports", "precision", "range", "Range", True, "rifle,pistol,shotgun", "ranked,casual", "mmr,score"),
    ("chess", "Catur", "Chess", "precision", "hall", "Board", True, "rapid,blitz,classical,bullet", "ranked,casual", "mmr,wins,losses,rating"),
    # ---------------- GYMNASTICS ----------------
    ("artistic-gymnastics", "Senam Artistik", "Artistic Gymnastics", "gymnastics", "gym", "Apparatus", True, "floor,pommel,vault,bars,beam", "ranked,casual", "mmr,score"),
    ("rhythmic-gymnastics", "Senam Ritmik", "Rhythmic Gymnastics", "gymnastics", "gym", "Mat Area", True, "hoop,ball,clubs,ribbon,rope", "ranked,casual", "mmr,score"),
    ("trampoline", "Trampolin", "Trampoline", "gymnastics", "gym", "Trampoline", True, "individual,synchronised", "ranked,casual", "mmr,score"),
    # ---------------- OUTDOOR / CLIMBING ----------------
    ("sport-climbing", "Panjat Sport", "Sport Climbing", "outdoor", "climbing-gym", "Wall", True, "lead,top_rope,speed", "ranked,casual", "mmr,grade"),
    ("bouldering", "Bouldering", "Bouldering", "outdoor", "climbing-gym", "Wall", True, "boulder", "ranked,casual", "mmr,grade"),
    ("rock-climbing", "Panjat Tebing", "Rock Climbing", "outdoor", "climbing-gym", "Wall", True, "trad,sport", "ranked,casual", "mmr,grade"),
    ("mountaineering", "Pendakian Gunung", "Mountaineering", "outdoor", "mountain", "Route", False, "expedition", "casual", "summits,elevation"),
    ("hiking", "Hiking", "Hiking", "outdoor", "trail", "Route", False, "day,overnight", "casual", "distance,elevation"),
    ("trekking", "Trekking", "Trekking", "outdoor", "trail", "Route", False, "multi_day", "casual", "distance,elevation"),
    # ---------------- OTHER RECOGNIZED ----------------
    ("sepak-takraw", "Sepak Takraw", "Sepak Takraw", "other", "court", "Court", True, "regu,doubles", "ranked,casual", "mmr,wins,losses"),
    ("equestrian", "Berkuda", "Equestrian", "other", "arena", "Arena", True, "dressage,jumping", "ranked,casual", "mmr,score"),
    ("skateboarding", "Skateboard", "Skateboarding", "other", "park", "Park", True, "street,park", "ranked,casual", "mmr,score"),
    ("roller-skating", "Sepatu Roda", "Roller Skating", "other", "track", "Track", True, "speed,artistic", "ranked,casual", "mmr,time_pb"),
]


def _csv(v: str) -> list[str]:
    return [x for x in v.split(",") if x]


SPORTS_PAYLOAD: list[dict[str, object]] = [
    {
        "slug": slug,
        "label_id": label_id,
        "label_en": label_en,
        "category": category,
        "venue_kind": venue_kind,
        "resource_label": resource_label,
        "competitive": competitive,
        "variants": _csv(variants),
        "formats": _csv(formats),
        "metrics": _csv(metrics),
    }
    for (
        slug,
        label_id,
        label_en,
        category,
        venue_kind,
        resource_label,
        competitive,
        variants,
        formats,
        metrics,
    ) in _S
]

SPORT_BY_SLUG: dict[str, dict[str, object]] = {row["slug"]: row for row in SPORTS_PAYLOAD}
SPORT_SLUGS: frozenset[str] = frozenset(SPORT_BY_SLUG)
SPORT_CATEGORY_SLUGS: frozenset[str] = frozenset(c[0] for c in SPORT_CATEGORIES)
CATEGORY_SPORTS: dict[str, list[str]] = {
    c[0]: [row["slug"] for row in SPORTS_PAYLOAD if row["category"] == c[0]]
    for c in SPORT_CATEGORIES
}
