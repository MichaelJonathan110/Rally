"""Reference dataset: Indonesia's kota otonom (autonomous cities).

Master list of every autonomous city grouped by province, so the city
picker can offer ALL Indonesian cities - not just the ones that already
have seeded content. DKI Jakarta's five administrative cities are unified
into a single "Jakarta" entry (the app's canonical spelling).

Kept dependency-free so it can be imported by the seed script, the API and
(indirectly) the web app without a database round-trip.
"""
from __future__ import annotations

#: (city, province) - sorted by city name.
CITIES: list[tuple[str, str]] = [
    ("Ambon", "Maluku"),
    ("Balikpapan", "Kalimantan Timur"),
    ("Banda Aceh", "Aceh"),
    ("Bandar Lampung", "Lampung"),
    ("Bandung", "Jawa Barat"),
    ("Banjar", "Jawa Barat"),
    ("Banjarbaru", "Kalimantan Selatan"),
    ("Banjarmasin", "Kalimantan Selatan"),
    ("Batam", "Kepulauan Riau"),
    ("Batu", "Jawa Timur"),
    ("Baubau", "Sulawesi Tenggara"),
    ("Bekasi", "Jawa Barat"),
    ("Bengkulu", "Bengkulu"),
    ("Bima", "Nusa Tenggara Barat"),
    ("Binjai", "Sumatera Utara"),
    ("Bitung", "Sulawesi Utara"),
    ("Blitar", "Jawa Timur"),
    ("Bogor", "Jawa Barat"),
    ("Bontang", "Kalimantan Timur"),
    ("Bukittinggi", "Sumatera Barat"),
    ("Cilegon", "Banten"),
    ("Cimahi", "Jawa Barat"),
    ("Cirebon", "Jawa Barat"),
    ("Denpasar", "Bali"),
    ("Depok", "Jawa Barat"),
    ("Dumai", "Riau"),
    ("Gorontalo", "Gorontalo"),
    ("Gunungsitoli", "Sumatera Utara"),
    ("Jakarta", "Daerah Khusus Ibukota Jakarta"),
    ("Jambi", "Jambi"),
    ("Jayapura", "Papua"),
    ("Kediri", "Jawa Timur"),
    ("Kendari", "Sulawesi Tenggara"),
    ("Kotamobagu", "Sulawesi Utara"),
    ("Kupang", "Nusa Tenggara Timur"),
    ("Langsa", "Aceh"),
    ("Lhokseumawe", "Aceh"),
    ("Lubuk Linggau", "Sumatera Selatan"),
    ("Madiun", "Jawa Timur"),
    ("Magelang", "Jawa Tengah"),
    ("Makassar", "Sulawesi Selatan"),
    ("Malang", "Jawa Timur"),
    ("Manado", "Sulawesi Utara"),
    ("Mataram", "Nusa Tenggara Barat"),
    ("Medan", "Sumatera Utara"),
    ("Metro", "Lampung"),
    ("Mojokerto", "Jawa Timur"),
    ("Padang", "Sumatera Barat"),
    ("Padang Panjang", "Sumatera Barat"),
    ("Padangsidimpuan", "Sumatera Utara"),
    ("Pagar Alam", "Sumatera Selatan"),
    ("Palangka Raya", "Kalimantan Tengah"),
    ("Palembang", "Sumatera Selatan"),
    ("Palopo", "Sulawesi Selatan"),
    ("Palu", "Sulawesi Tengah"),
    ("Pangkalpinang", "Kepulauan Bangka Belitung"),
    ("Parepare", "Sulawesi Selatan"),
    ("Pariaman", "Sumatera Barat"),
    ("Pasuruan", "Jawa Timur"),
    ("Payakumbuh", "Sumatera Barat"),
    ("Pekalongan", "Jawa Tengah"),
    ("Pekanbaru", "Riau"),
    ("Pematangsiantar", "Sumatera Utara"),
    ("Pontianak", "Kalimantan Barat"),
    ("Prabumulih", "Sumatera Selatan"),
    ("Probolinggo", "Jawa Timur"),
    ("Sabang", "Aceh"),
    ("Salatiga", "Jawa Tengah"),
    ("Samarinda", "Kalimantan Timur"),
    ("Sawahlunto", "Sumatera Barat"),
    ("Semarang", "Jawa Tengah"),
    ("Serang", "Banten"),
    ("Sibolga", "Sumatera Utara"),
    ("Singkawang", "Kalimantan Barat"),
    ("Solok", "Sumatera Barat"),
    ("Sorong", "Papua Barat Daya"),
    ("Subulussalam", "Aceh"),
    ("Sukabumi", "Jawa Barat"),
    ("Sungai Penuh", "Jambi"),
    ("Surabaya", "Jawa Timur"),
    ("Surakarta", "Jawa Tengah"),
    ("Tangerang", "Banten"),
    ("Tangerang Selatan", "Banten"),
    ("Tanjungbalai", "Sumatera Utara"),
    ("Tanjungpinang", "Kepulauan Riau"),
    ("Tarakan", "Kalimantan Utara"),
    ("Tasikmalaya", "Jawa Barat"),
    ("Tebing Tinggi", "Sumatera Utara"),
    ("Tegal", "Jawa Tengah"),
    ("Ternate", "Maluku Utara"),
    ("Tidore Kepulauan", "Maluku Utara"),
    ("Tomohon", "Sulawesi Utara"),
    ("Tual", "Maluku"),
    ("Yogyakarta", "Daerah Istimewa Yogyakarta"),
]

#: Canonical province order (geographic, west -> east) for stable UI ordering.
PROVINCE_ORDER: list[str] = [
    "Aceh",
    "Sumatera Utara",
    "Sumatera Barat",
    "Riau",
    "Kepulauan Riau",
    "Jambi",
    "Sumatera Selatan",
    "Kepulauan Bangka Belitung",
    "Bengkulu",
    "Lampung",
    "Banten",
    "Daerah Khusus Ibukota Jakarta",
    "Jawa Barat",
    "Jawa Tengah",
    "Daerah Istimewa Yogyakarta",
    "Jawa Timur",
    "Bali",
    "Nusa Tenggara Barat",
    "Nusa Tenggara Timur",
    "Kalimantan Barat",
    "Kalimantan Tengah",
    "Kalimantan Selatan",
    "Kalimantan Timur",
    "Kalimantan Utara",
    "Sulawesi Utara",
    "Gorontalo",
    "Sulawesi Tengah",
    "Sulawesi Selatan",
    "Sulawesi Tenggara",
    "Maluku",
    "Maluku Utara",
    "Papua",
    "Papua Barat Daya",
]

#: city -> province.
CITY_PROVINCE: dict[str, str] = {city: province for city, province in CITIES}

#: Legacy / alias spellings normalised to the canonical picker name.
CITY_ALIASES: dict[str, str] = {
    "Solo": "Surakarta",
    "Jogja": "Yogyakarta",
    "Jogjakarta": "Yogyakarta",
    "DKI Jakarta": "Jakarta",
    "Jakarta Pusat": "Jakarta",
    "Jakarta Selatan": "Jakarta",
    "Jakarta Timur": "Jakarta",
    "Jakarta Barat": "Jakarta",
    "Jakarta Utara": "Jakarta",
}

#: All city names (canonical).
CITY_NAMES: list[str] = [city for city, _ in CITIES]

#: province -> [cities] (canonical order).
PROVINCES: dict[str, list[str]] = {}
for _city, _province in CITIES:
    PROVINCES.setdefault(_province, []).append(_city)


def canonical_city(name: str) -> str:
    """Map a legacy/alias city name to its canonical picker spelling."""
    return CITY_ALIASES.get(name, name)


def province_of(name: str) -> str | None:
    """Province for a city (after alias normalisation), if known."""
    return CITY_PROVINCE.get(canonical_city(name))

