"""Demo venue catalog: venue<->activity-type matched venues across Indonesia.

Every row is (city, area, activity_type, venue_name). A venue is created for ONE
specific activity type and only ever hosts activities of that type, so a 'musik'
activity can never appear at a padel court. ``area`` is the kecamatan/kawasan.

Sport-awareness (see :mod:`app.core.sports`): each venue is projected into a
:class:`CatalogVenue` carrying a REAL primary name, its city (rendered as
``"<city>, Indonesia"``), the sport slugs it supports and the typed *resources*
(venue_kind + resource_label) that the booking engine reserves. ``VENUE_ROWS``
is kept as the legacy 4-tuple view consumed by ``scripts/seed.py``.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

#: Flagship RALLY-branded venues with REAL primary names. They lead the catalog
#: and give the demo a recognisable brand presence in major metros.
_FLAGSHIP_VENUE_ROWS: list[tuple[str, str, str, str]] = [
    ("Tangerang", "BSD", "padel", "RALLY Padel Arena"),
    ("Jakarta", "Senayan", "tenis", "RALLY Tennis Center Senayan"),
    ("Bandung", "Dago", "gym", "RALLY Strength Lab Bandung"),
    ("Surabaya", "Darmo", "futsal", "RALLY Futsal Dome Surabaya"),
    ("Denpasar", "Sanur", "renang", "RALLY Aquatic Center Bali"),
]

_CURATED_VENUE_ROWS: list[tuple[str, str, str, str]] = [
    # --- DKI Jakarta ---
    ("Jakarta", "Kemang", "kopdar", "Kopi Kemang Raya"),
    ("Jakarta", "Senayan", "gym", "Senayan Sports Club"),
    ("Jakarta", "Cilandak", "padel", "Jungle Padel Jakarta"),
    ("Jakarta", "Tebet", "billiard", "Mille Billiard Tebet"),
    ("Jakarta", "Bulungan", "badminton", "GOR Bulungan"),
    # --- Jawa Barat ---
    ("Bandung", "Cihampelas", "lari", "Lapangan Cihampelas"),
    ("Bandung", "Dago", "yoga", "Dago Yoga Studio"),
    ("Bandung", "Buah Batu", "futsal", "GOR Buah Batu"),
    ("Bekasi", "Harapan Indah", "futsal", "GOR Harapan Indah"),
    ("Bekasi", "Grand Wisata", "gym", "Grand Wisata Fitness"),
    ("Bekasi", "Summarecon", "basket", "Summarecon Basketball Court"),
    ("Bogor", "Pajajaran", "lari", "Taman Pajajaran"),
    ("Bogor", "Dramaga", "badminton", "GOR Dramaga"),
    ("Bogor", "Puncak", "hiking", "Jalur Puncak"),
    ("Depok", "Margonda", "gym", "Margonda Fitness Center"),
    ("Depok", "Kukusan", "lari", "Danau UI"),
    ("Depok", "Cinere", "padel", "Cinere Padel Club"),
    ("Cirebon", "Grage", "lari", "Lapangan Grage"),
    ("Cirebon", "Kejaksan", "badminton", "GOR Kejaksan"),
    ("Tasikmalaya", "Dadaha", "badminton", "GOR Dadaha"),
    ("Tasikmalaya", "Alun-Alun", "lari", "Alun-Alun Tasikmalaya"),
    # --- Banten ---
    ("Tangerang", "Karawaci", "futsal", "GOR Karawaci"),
    ("Tangerang", "Cikokol", "kopdar", "Kopi Cikokol"),
    ("Tangerang Selatan", "BSD", "padel", "BSD Padel Arena"),
    ("Tangerang Selatan", "Bintaro", "gym", "Bintaro Fitness Hub"),
    ("Serang", "Ciceri", "badminton", "GOR Ciceri"),
    ("Cilegon", "Krakatau", "lari", "Stadion Krakatau Steel"),
    # --- Jawa Tengah ---
    ("Semarang", "Simpang Lima", "lari", "Lapangan Simpang Lima"),
    ("Semarang", "Tembalang", "gym", "Tembalang Fitness"),
    ("Semarang", "Kota Lama", "kopdar", "Kopi Kota Lama"),
    ("Surakarta", "Manahan", "lari", "Stadion Manahan"),
    ("Surakarta", "Solo Baru", "basket", "Solo Paragon Arena"),
    ("Magelang", "Alun-Alun", "badminton", "GOR Magelang"),
    ("Pekalongan", "Kajen", "badminton", "GOR Pekalongan"),
    ("Tegal", "Alun-Alun", "lari", "Alun-Alun Tegal"),
    ("Salatiga", "Diponegoro", "gym", "Salatiga Sport Center"),
    # --- DI Yogyakarta ---
    ("Yogyakarta", "Malioboro", "kopdar", "Kopi Malioboro"),
    ("Yogyakarta", "Umbulharjo", "padel", "UGM Padel Center"),
    ("Yogyakarta", "Kotabaru", "basket", "GOR Among Rogo"),
    # --- Jawa Timur ---
    ("Surabaya", "Gubeng", "badminton", "GOR Gubeng"),
    ("Surabaya", "Darmo", "futsal", "Lapangan Darmo"),
    ("Surabaya", "Kenjeran", "lari", "Kenjeran Park"),
    ("Malang", "Ijen", "lari", "Lapangan Ijen"),
    ("Malang", "Soekarno-Hatta", "futsal", "GOR Malang"),
    ("Kediri", "Simpang Lima", "badminton", "GOR Kediri"),
    ("Madiun", "Alun-Alun", "lari", "Alun-Alun Madiun"),
    ("Probolinggo", "Mayangan", "futsal", "GOR Probolinggo"),
    ("Pasuruan", "Alun-Alun", "badminton", "GOR Pasuruan"),
    # --- Bali and Nusa Tenggara ---
    ("Denpasar", "Renon", "padel", "Renon Padel Bali"),
    ("Denpasar", "Sanur", "lari", "Pantai Sanur"),
    ("Mataram", "Senggigi", "lari", "Pantai Senggigi"),
    ("Mataram", "Cakranegara", "badminton", "GOR Cakranegara"),
    ("Bima", "Alun-Alun", "futsal", "GOR Bima"),
    ("Kupang", "Oebobo", "badminton", "Kupang Sport Center"),
    ("Kupang", "Lasiana", "lari", "Pantai Lasiana"),
    # --- Sumatera ---
    ("Medan", "Kesawan", "kopdar", "Kopi Kesawan"),
    ("Medan", "Polonia", "padel", "Polonia Padel Medan"),
    ("Medan", "Petisah", "billiard", "Mille Billiard Medan"),
    ("Binjai", "Alun-Alun", "futsal", "GOR Binjai"),
    ("Pematangsiantar", "Siantar", "badminton", "GOR Siantar"),
    ("Padang", "Pantai Padang", "lari", "Pantai Padang"),
    ("Padang", "Air Manis", "yoga", "Air Manis Yoga"),
    ("Bukittinggi", "Jam Gadang", "lari", "Jam Gadang"),
    ("Pekanbaru", "Sudirman", "futsal", "GOR Sudirman"),
    ("Pekanbaru", "Rumbai", "badminton", "GOR Rumbai"),
    ("Batam", "Nagoya", "kopdar", "Kopi Nagoya"),
    ("Batam", "Batu Aji", "gym", "Batam Fitness Center"),
    ("Tanjungpinang", "Alun-Alun", "lari", "Alun-Alun Tanjungpinang"),
    ("Dumai", "Simpang", "futsal", "GOR Dumai"),
    ("Jambi", "Tugu Juang", "lari", "Tugu Juang"),
    ("Sungai Penuh", "Alun-Alun", "badminton", "GOR Sungai Penuh"),
    ("Palembang", "Benteng Kuto Besak", "lari", "Benteng Kuto Besak"),
    ("Palembang", "Ilir", "padel", "Palembang Padel Club"),
    ("Lubuk Linggau", "Alun-Alun", "futsal", "GOR Lubuk Linggau"),
    ("Pagar Alam", "Alun-Alun", "badminton", "GOR Pagar Alam"),
    ("Prabumulih", "Alun-Alun", "lari", "Alun-Alun Prabumulih"),
    ("Bandar Lampung", "Kedaton", "futsal", "GOR Kedaton"),
    ("Bandar Lampung", "Way Halim", "lari", "Taman Way Halim"),
    ("Metro", "Alun-Alun", "badminton", "GOR Metro"),
    ("Bengkulu", "Pantai Panjang", "lari", "Pantai Panjang"),
    ("Bengkulu", "Simpang", "futsal", "GOR Bengkulu"),
    ("Banda Aceh", "Blang Padang", "lari", "Lapangan Blang Padang"),
    ("Banda Aceh", "Ulee Lheue", "padel", "Banda Aceh Padel"),
    ("Langsa", "Alun-Alun", "badminton", "GOR Langsa"),
    ("Lhokseumawe", "Alun-Alun", "futsal", "GOR Lhokseumawe"),
    ("Sabang", "Iboih", "hiking", "Jalur Iboih"),
    ("Subulussalam", "Alun-Alun", "badminton", "GOR Subulussalam"),
    ("Medan", "Sunggal", "basket", "Sunggal Basketball"),
    # --- Kalimantan ---
    ("Pontianak", "Khatulistiwa", "lari", "Tugu Khatulistiwa"),
    ("Pontianak", "Ahmad Yani", "badminton", "GOR Pontianak"),
    ("Singkawang", "Alun-Alun", "futsal", "GOR Singkawang"),
    ("Banjarmasin", "Siring", "lari", "Menara Pandang Siring"),
    ("Banjarmasin", "Kayu Tangi", "badminton", "GOR Kayu Tangi"),
    ("Banjarbaru", "Alun-Alun", "futsal", "GOR Banjarbaru"),
    ("Palangka Raya", "Bundaran Besar", "lari", "Bundaran Besar"),
    ("Palangka Raya", "Kahayan", "badminton", "GOR Kahayan"),
    ("Samarinda", "Tepian Mahakam", "lari", "Tepian Mahakam"),
    ("Samarinda", "Sempaja", "futsal", "GOR Sempaja"),
    ("Balikpapan", "Pantai Klandasan", "lari", "Pantai Klandasan"),
    ("Balikpapan", "Sepinggan", "padel", "Balikpapan Padel Club"),
    ("Bontang", "Alun-Alun", "futsal", "GOR Bontang"),
    ("Tarakan", "Tengah", "badminton", "GOR Tarakan"),
    # --- Sulawesi ---
    ("Makassar", "Losari", "lari", "Pantai Losari"),
    ("Makassar", "Panakkukang", "padel", "Panakkukang Padel"),
    ("Makassar", "Gunung Sari", "badminton", "GOR Gunung Sari"),
    ("Parepare", "Alun-Alun", "futsal", "GOR Parepare"),
    ("Palopo", "Alun-Alun", "badminton", "GOR Palopo"),
    ("Palu", "Talise", "lari", "Pantai Talise"),
    ("Palu", "Tatura", "futsal", "GOR Tatura"),
    ("Kendari", "Kendari Beach", "lari", "Pantai Kendari"),
    ("Kendari", "Manding", "badminton", "GOR Manding"),
    ("Baubau", "Alun-Alun", "futsal", "GOR Baubau"),
    ("Manado", "Boulevard", "lari", "Boulevard Manado"),
    ("Manado", "Megamas", "padel", "Manado Padel Center"),
    ("Bitung", "Alun-Alun", "futsal", "GOR Bitung"),
    ("Tomohon", "Alun-Alun", "badminton", "GOR Tomohon"),
    ("Kotamobagu", "Alun-Alun", "futsal", "GOR Kotamobagu"),
    ("Gorontalo", "Alun-Alun", "lari", "Alun-Alun Gorontalo"),
    ("Gorontalo", "Dungingi", "badminton", "GOR Dungingi"),
    # --- Maluku dan Papua ---
    ("Ambon", "Pantai Natsepa", "lari", "Pantai Natsepa"),
    ("Ambon", "Sirimau", "badminton", "GOR Sirimau"),
    ("Tual", "Alun-Alun", "futsal", "GOR Tual"),
    ("Ternate", "Alun-Alun", "lari", "Alun-Alun Ternate"),
    ("Ternate", "Sasa", "badminton", "GOR Sasa"),
    ("Tidore Kepulauan", "Alun-Alun", "futsal", "GOR Tidore"),
    ("Jayapura", "Pantai Base G", "lari", "Pantai Base G"),
    ("Jayapura", "Abepura", "badminton", "GOR Abepura"),
    ("Sorong", "Alun-Alun", "futsal", "GOR Sorong"),
    # --- extra city fillers ---
    ("Batu", "Alun-Alun", "lari", "Alun-Alun Batu"),
    ("Blitar", "Alun-Alun", "badminton", "GOR Blitar"),
    ("Mojokerto", "Alun-Alun", "futsal", "GOR Mojokerto"),
    ("Sukabumi", "Alun-Alun", "badminton", "GOR Sukabumi"),
    ("Cimahi", "Alun-Alun", "lari", "Alun-Alun Cimahi"),
    ("Banjar", "Alun-Alun", "futsal", "GOR Banjar"),
    ("Padang Panjang", "Alun-Alun", "badminton", "GOR Padang Panjang"),
    ("Payakumbuh", "Alun-Alun", "lari", "Alun-Alun Payakumbuh"),
    ("Pariaman", "Alun-Alun", "futsal", "GOR Pariaman"),
    ("Solok", "Alun-Alun", "badminton", "GOR Solok"),
    ("Sawahlunto", "Alun-Alun", "lari", "Alun-Alun Sawahlunto"),
    ("Padangsidimpuan", "Alun-Alun", "futsal", "GOR Padangsidimpuan"),
    ("Sibolga", "Alun-Alun", "lari", "Pantai Sibolga"),
    ("Tanjungbalai", "Alun-Alun", "badminton", "GOR Tanjungbalai"),
    ("Tebing Tinggi", "Alun-Alun", "futsal", "GOR Tebing Tinggi"),
    ("Gunungsitoli", "Alun-Alun", "lari", "Alun-Alun Gunungsitoli"),
    ("Pangkalpinang", "Alun-Alun", "badminton", "GOR Pangkalpinang"),
    # --- Combat / strength / gymnastics / winter ---
    ('Jakarta', 'Kemang', 'boxing', 'Jakarta Boxing Camp Kemang'),
    ('Jakarta', 'Tebet', 'muay-thai', 'Muay Thai Jakarta Tebet'),
    ('Jakarta', 'Sudirman', 'mma', 'Jakarta MMA Academy Sudirman'),
    ('Bandung', 'Dago', 'bjj', 'Bandung BJJ Dago'),
    ('Bandung', 'Cihampelas', 'judo', 'Bandung Judo Dojo Cihampelas'),
    ('Surabaya', 'Gubeng', 'karate', 'Surabaya Karate Dojo Gubeng'),
    ('Surabaya', 'Darmo', 'taekwondo', 'Surabaya Taekwondo Center Darmo'),
    ('Semarang', 'Tembalang', 'wrestling', 'Semarang Wrestling Gym Tembalang'),
    ('Yogyakarta', 'Kotabaru', 'boxing', 'Yogyakarta Boxing Ring Kotabaru'),
    ('Medan', 'Polonia', 'muay-thai', 'Medan Muay Thai Camp Polonia'),
    ('Makassar', 'Panakkukang', 'mma', 'Makassar MMA Gym Panakkukang'),
    ('Denpasar', 'Renon', 'bjj', 'Bali BJJ Renon'),
    ('Jakarta', 'Senayan', 'weightlifting', 'Senayan Weightlifting Hall'),
    ('Bandung', 'Buah Batu', 'powerlifting', 'Bandung Powerlifting Club'),
    ('Surabaya', 'Kenjeran', 'crossfit', 'Surabaya CrossFit Box Kenjeran'),
    ('Tangerang', 'Bintaro', 'calisthenics', 'Bintaro Calisthenics Park'),
    ('Jakarta', 'Cilandak', 'artistic-gymnastics', 'Jakarta Artistic Gymnastics Center'),
    ('Bandung', 'Dago', 'rhythmic-gymnastics', 'Bandung Rhythmic Gymnastics Studio'),
    ('Surabaya', 'Gubeng', 'trampoline', 'Surabaya Trampoline Park Gubeng'),
    ('Jakarta', 'Senayan', 'figure-skating', 'Senayan Ice Rink'),
    ('Jakarta', 'Kemang', 'ice-hockey', 'Jakarta Ice Hockey Arena Kemang'),
    ('Bandung', 'Dago', 'skiing', 'Bandung Ski Slope Dago'),
    ('Bogor', 'Puncak', 'snowboarding', 'Puncak Snowboard Park'),
    # --- Other recognised sports ---
    ('Jakarta', 'Senayan', 'sepak-takraw', 'Jakarta Sepak Takraw Arena'),
    ('Bandung', 'Dago', 'skateboarding', 'Bandung Skate Park Dago'),
    ('Jakarta', 'Cilandak', 'equestrian', 'Jakarta Equestrian Arena'),
    ('Surabaya', 'Gubeng', 'roller-skating', 'Surabaya Roller Skating Track'),
    # --- Cycling (balanced fill) ---
    ("Jakarta", "Senayan", "road-cycling", "Jakarta Road Cycling Hub Senayan"),
    ("Bandung", "Lembang", "mountain-biking", "Lembang Mountain Bike Trail"),
    ("Yogyakarta", "Sleman", "road-cycling", "Sleman Road Cycling Circuit"),
    ("Jakarta", "Cilandak", "bmx", "Cilandak BMX Track"),
    ("Surabaya", "Kenjeran", "track-cycling", "Kenjeran Velodrome"),
    ("Bogor", "Sentul", "gravel-cycling", "Sentul Gravel Cycling Park"),
    ("Malang", "Batu", "mountain-biking", "Batu Downhill MTB Park"),
    ("Semarang", "Simpang Lima", "bmx", "Semarang BMX Arena"),
    ("Denpasar", "Canggu", "gravel-cycling", "Canggu Gravel Ride Hub"),
    # --- Water (balanced fill) ---
    ("Jakarta", "Ancol", "swimming", "Ancol Aquatic Center"),
    ("Denpasar", "Sanur", "open-water-swimming", "Sanur Open Water Swim"),
    ("Denpasar", "Kuta", "surfing", "Kuta Surf School"),
    ("Bandung", "Dago", "swimming", "Dago Swimming Pool"),
    ("Makassar", "Losari", "surfing", "Losari Beach Surf Point"),
    ("Jakarta", "Lubang Buaya", "diving", "Jakarta Diving Academy"),
    ("Palembang", "Musi", "rowing", "Musi River Rowing Club"),
    ("Batam", "Nongsa", "kayaking", "Nongsa Kayak Center"),
    ("Pontianak", "Kapuas", "canoeing", "Kapuas Canoe Club"),
    ("Surabaya", "Kenjeran", "sailing", "Kenjeran Sailing Marina"),
    # --- Precision (balanced fill) ---
    ("Jakarta", "Cibubur", "archery", "Cibubur Archery Range"),
    ("Bandung", "Dago", "archery", "Dago Archery Club"),
    ("Jakarta", "Tebet", "shooting", "Tebet Shooting Range"),
    ("Surabaya", "Gubeng", "billiards", "Gubeng Billiard Hall"),
    ("Yogyakarta", "Malioboro", "darts", "Malioboro Darts Lounge"),
    ("Medan", "Polonia", "bowling", "Polonia Bowling Center"),
    ("Jakarta", "Pondok Indah", "golf", "Pondok Indah Golf Course"),
    ("Bogor", "Rancamaya", "golf", "Rancamaya Golf Estate"),
    # --- Other (balanced fill) ---
    ("Jakarta", "Senayan", "sepak-takraw", "Senayan Sepak Takraw Court"),
    ("Palembang", "Jakabaring", "sepak-takraw", "Jakabaring Takraw Arena"),
    ("Bogor", "Cibodas", "equestrian", "Cibodas Equestrian Park"),
    ("Bandung", "Sabuga", "skateboarding", "Sabuga Skate Plaza"),
    ("Surabaya", "Tunjungan", "skateboarding", "Tunjungan Skate Spot"),
    ("Yogyakarta", "Alun Alun", "roller-skating", "Alun Alun Roller Rink"),
    # --- Gymnastics (top up, never reduced) ---
    ("Jakarta", "Senayan", "artistic-gymnastics", "Senayan Gymnastics Center"),
    ("Bandung", "Dago", "artistic-gymnastics", "Dago Gymnastics Hall"),
    ("Surabaya", "Darmo", "rhythmic-gymnastics", "Darmo Rhythmic Gymnastics Studio"),
    ("Jakarta", "Kemang", "rhythmic-gymnastics", "Kemang Rhythmic Studio"),
    ("Yogyakarta", "Sleman", "trampoline", "Sleman Trampoline Park"),
    # --- Winter (top up, never reduced) ---
    ("Jakarta", "Cilandak", "skiing", "Jakarta Indoor Ski Slope"),
    ("Bandung", "Lembang", "skiing", "Lembang Snow Slope"),
    ("Jakarta", "Tebet", "snowboarding", "Tebet Snowboard Park"),
    ("Bogor", "Puncak", "snowboarding", "Puncak Snowboard Arena"),
    ("Surabaya", "Darmo", "ice-hockey", "Darmo Ice Rink"),
    # --- Strength (balanced fill) ---
    ("Jakarta", "Senayan", "crossfit", "Senayan CrossFit Box"),
    ("Bandung", "Dago", "calisthenics", "Dago Calisthenics Park"),
    ("Surabaya", "Gubeng", "powerlifting", "Gubeng Powerlifting Gym"),
    ("Medan", "Polonia", "weightlifting", "Polonia Weightlifting Club"),
    ("Makassar", "Losari", "strongman", "Losari Strongman Yard"),
    ("Yogyakarta", "Malioboro", "bodybuilding", "Malioboro Bodybuilding Gym"),
    # --- Outdoor (balanced fill) ---
    ("Bogor", "Puncak", "hiking", "Puncak Hiking Trail"),
    ("Yogyakarta", "Sleman", "trail-running", "Sleman Trail Running Course"),
    ("Bandung", "Lembang", "rock-climbing", "Lembang Rock Climbing Wall"),
    ("Malang", "Batu", "mountaineering", "Batu Mountaineering Base"),
    ("Denpasar", "Bedugul", "trekking", "Bedugul Trekking Path"),
    ("Surabaya", "Kenjeran", "bouldering", "Kenjeran Bouldering Gym"),
]


# --- Deterministic per-city expansion -------------------------------------
# The curated rows above are real, hand-picked venues. Every autonomous city
# (see app.core.cities) must offer at least 6 activities, so for each city we
# top the catalog up to 6 venues with a *deterministic* RNG (fixed seed ->
# identical output on every run/import). Filler venues always embed the city
# name, so names stay globally unique and obviously per-city.

import random as _random  # noqa: E402

from app.core.cities import CITY_PROVINCE  # noqa: E402
from app.core.sports import SPORTS_PAYLOAD, SPORT_BY_SLUG, SPORT_SLUGS  # noqa: E402

#: One activity type per high-level category -> every city gets a spread of
#: categories (sports/fitness/outdoor/games/social/creative) instead of six
#: near-identical sports courts.
_CATEGORY_TYPE_POOL: dict[str, tuple[str, ...]] = {
    "sports": ("padel", "badminton", "basket", "billiard", "futsal", "tenis", "renang"),
    "fitness": ("lari", "gym", "yoga", "sepeda"),
    "outdoor": ("hiking", "gowes", "panjat", "camping"),
    "games": ("boardgame", "esport"),
    "social": ("kopdar", "nobar"),
    "creative": ("musik", "seni", "sketsa"),
}

#: Plausible Indonesian kawasan / street names usable in any city.
_AREA_POOL: tuple[str, ...] = (
    "Pusat Kota", "Taman Kota", "Riverside", "City Center", "Pasar Baru",
    "Merdeka", "Sudirman", "Diponegoro", "Ahmad Yani", "Veteran", "Pemuda",
    "Kartini", "Cendrawasih", "Melati", "Kenanga", "Anggrek", "Hayam Wuruk",
    "Gajah Mada", "Pahlawan", "Sisingamangaraja", "Imam Bonjol", "Cut Nyak Dien",
)

#: Venue-name templates per activity type; both {area} and {city} are filled so
#: the name reads plausibly and stays unique across the whole country.
_VENUE_NAME_TPL: dict[str, tuple[str, ...]] = {
    "padel": ("Padel Arena {area} {city}",),
    "badminton": ("GOR Badminton {area} {city}",),
    "basket": ("GOR Basket {area} {city}",),
    "billiard": ("Billiard Center {area} {city}",),
    "futsal": ("GOR Futsal {area} {city}",),
    "tenis": ("Lapangan Tenis {area} {city}",),
    "renang": ("Kolam Renang {area} {city}",),
    "lari": ("Lapangan Lari {area} {city}",),
    "gym": ("Fitness Center {area} {city}",),
    "yoga": ("Yoga Studio {area} {city}",),
    "sepeda": ("Rute Sepeda {area} {city}",),
    "hiking": ("Jalur Hiking {area} {city}",),
    "gowes": ("Titik Gowes {area} {city}",),
    "panjat": ("Wall Climbing {area} {city}",),
    "camping": ("Bumi Perkemahan {area} {city}",),
    "boardgame": ("Board Game Cafe {area} {city}",),
    "esport": ("E-Sport Arena {area} {city}",),
    "kopdar": ("Kopi {area} {city}",),
    "nobar": ("Nobar Spot {area} {city}",),
    "musik": ("Studio Musik {area} {city}",),
    "seni": ("Sanggar Seni {area} {city}",),
    "sketsa": ("Studio Sketsa {area} {city}",),
}

#: Target venues (hence activities) per city.
TARGET_VENUES_PER_CITY = 6

#: Fixed seed -> the generated tail is byte-for-byte reproducible.
_CATALOG_SEED = 20261002


def _expand_to_target(
    curated: list[tuple[str, str, str, str]],
    *,
    target: int = TARGET_VENUES_PER_CITY,
    seed: int = _CATALOG_SEED,
) -> list[tuple[str, str, str, str]]:
    """Append deterministic filler venues so every city reaches ``target``.

    Existing curated rows are preserved verbatim. For each under-served city we
    add venues whose types are drawn one-per-category first (so a city never
    ends up with six sports courts), then topped up from the remaining pool.
    """
    rows = list(curated)
    used_names = {name for _c, _a, _t, name in rows}
    by_city: dict[str, list[str]] = {}
    for city, _area, atype, _name in rows:
        by_city.setdefault(city, []).append(atype)

    rng = _random.Random(seed)
    all_types = tuple(_VENUE_NAME_TPL)
    for city in sorted(CITY_PROVINCE):
        existing = by_city.setdefault(city, [])
        need = target - len(existing)
        if need <= 0:
            continue
        used_types = set(existing)
        chosen: list[str] = []

        categories = list(_CATEGORY_TYPE_POOL)
        rng.shuffle(categories)
        for category in categories:
            if len(chosen) >= need:
                break
            options = [
                t for t in _CATEGORY_TYPE_POOL[category]
                if t not in used_types and t not in chosen
            ]
            if options:
                chosen.append(rng.choice(options))

        remaining = [
            t for t in all_types if t not in used_types and t not in chosen
        ]
        while len(chosen) < need and remaining:
            pick = rng.choice(remaining)
            chosen.append(pick)
            remaining.remove(pick)

        for atype in chosen:
            area = rng.choice(_AREA_POOL)
            base = _VENUE_NAME_TPL[atype][0].format(area=area, city=city)
            name = base
            suffix = 2
            while name in used_names:
                name = f"{base} #{suffix}"
                suffix += 1
            used_names.add(name)
            rows.append((city, area, atype, name))

    return rows


#: Public catalog consumed by scripts/seed.py: curated venues + deterministic
#: per-city fillers (every one of the 94 cities ends with >= TARGET venues).
VENUE_ROWS: list[tuple[str, str, str, str]] = _expand_to_target(
    _FLAGSHIP_VENUE_ROWS + _CURATED_VENUE_ROWS
)



# --- Sport-awareness -------------------------------------------------------
#: Activity type -> the sport slugs (app.core.sports) it serves. Activity types
#: that are not sports (kopdar, musik, ...) map to no sport.
ACTIVITY_TYPE_SPORTS: dict[str, tuple[str, ...]] = {
    "padel": ("padel",),
    "badminton": ("badminton",),
    "basket": ("basketball", "basketball-3x3"),
    "billiard": ("billiards", "pool", "snooker"),
    "futsal": ("futsal",),
    "tenis": ("tennis",),
    "renang": ("swimming", "water-polo"),
    "lari": ("running", "sprinting", "track-field"),
    "gym": ("crossfit", "bodybuilding", "calisthenics", "strongman"),
    "yoga": (),
    "sepeda": ("road-cycling",),
    "hiking": ("hiking",),
    "gowes": ("road-cycling",),
    "panjat": ("sport-climbing", "bouldering", "rock-climbing"),
    "camping": (),
    "boardgame": ("chess",),
    "esport": (),
    "kopdar": (),
    "nobar": (),
    "musik": (),
    "seni": (),
    "sketsa": (),
    'boxing': ('boxing',),
    'muay-thai': ('muay-thai',),
    'mma': ('mma',),
    'bjj': ('bjj',),
    'judo': ('judo',),
    'karate': ('karate',),
    'taekwondo': ('taekwondo',),
    'wrestling': ('wrestling',),
    'weightlifting': ('weightlifting',),
    'powerlifting': ('powerlifting',),
    'crossfit': ('crossfit',),
    'calisthenics': ('calisthenics',),
    'artistic-gymnastics': ('artistic-gymnastics',),
    'rhythmic-gymnastics': ('rhythmic-gymnastics',),
    'trampoline': ('trampoline',),
    'figure-skating': ('figure-skating',),
    'ice-hockey': ('ice-hockey',),
    'skiing': ('skiing',),
    'snowboarding': ('snowboarding',),
    'sepak-takraw': ('sepak-takraw',),
    'skateboarding': ('skateboarding',),
    'equestrian': ('equestrian',),
    'roller-skating': ('roller-skating',),
}

# Fail fast if the catalog ever references a sport slug that no longer exists.
for _atype, _slugs in ACTIVITY_TYPE_SPORTS.items():
    _unknown = [slug for slug in _slugs if slug not in SPORT_SLUGS]
    if _unknown:
        raise ValueError(
            f"venue_catalog: activity type {_atype!r} references unknown sport "
            f"slugs {_unknown}"
        )
del _atype, _slugs, _unknown


@dataclass(frozen=True)
class VenueResource:
    """A bookable resource (maps 1:1 to a VenueCourt row)."""

    kind: str
    label: str


@dataclass(frozen=True)
class CatalogVenue:
    """A sport-aware catalog venue: primary name + city + sports + resources."""

    primary_name: str
    city: str
    area: str
    activity_type: str
    sport_slugs: tuple[str, ...]
    resources: tuple[VenueResource, ...]

    @property
    def location(self) -> str:
        """City as the secondary line shown under the primary name."""
        return f"{self.city}, Indonesia"

    @property
    def venue_kind(self) -> str | None:
        return venue_kind_for_sports(self.sport_slugs)


def venue_kind_for_sports(sport_slugs: Iterable[str]) -> str | None:
    """First venue_kind declared by any of ``sport_slugs`` (None if no sport)."""
    for slug in sport_slugs:
        row = SPORT_BY_SLUG.get(slug)
        if row is not None:
            return str(row["venue_kind"])
    return None


def resource_label_for_kind(venue_kind: str | None) -> str | None:
    """The canonical resource_label for a venue_kind (e.g. "court" -> "Court").

    venue_kind -> resource_label is not 1:1 (e.g. "gym" serves Training Area,
    Platform, ...), so the first declared label is used as the default.
    """
    if venue_kind is None:
        return None
    for row in SPORTS_PAYLOAD:
        if row["venue_kind"] == venue_kind:
            return str(row["resource_label"])
    return None


def _resources_for(sport_slugs: Iterable[str]) -> tuple[VenueResource, ...]:
    """Distinct typed resources (kind + label) needed for ``sport_slugs``."""
    seen: set[tuple[str, str]] = set()
    out: list[VenueResource] = []
    for slug in sport_slugs:
        row = SPORT_BY_SLUG.get(slug)
        if row is None:
            continue
        kind = str(row["venue_kind"])
        label = str(row["resource_label"])
        if (kind, label) not in seen:
            seen.add((kind, label))
            out.append(VenueResource(kind=kind, label=label))
    return tuple(out)


def _build_catalog(rows: Iterable[tuple[str, str, str, str]]) -> list[CatalogVenue]:
    catalog: list[CatalogVenue] = []
    for city, area, atype, name in rows:
        slugs = ACTIVITY_TYPE_SPORTS.get(atype, ())
        catalog.append(
            CatalogVenue(
                primary_name=name,
                city=city,
                area=area,
                activity_type=atype,
                sport_slugs=tuple(slugs),
                resources=_resources_for(slugs),
            )
        )
    return catalog


#: Sport-aware projection of every catalog venue (one per VENUE_ROWS row).
VENUE_CATALOG: list[CatalogVenue] = _build_catalog(VENUE_ROWS)
VENUE_BY_NAME: dict[str, CatalogVenue] = {
    venue.primary_name: venue for venue in VENUE_CATALOG
}
