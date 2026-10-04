/**
 * SPORTS CATALOG - local mirror of apps/api/app/core/sports.py.
 *
 * Source of truth: the backend sports registry. This module is a faithful copy
 * of the 12 sport categories and 111 sports so the web app can render the whole
 * catalog offline, with no backend round-trip. When the live API is reachable,
 * `useSports()` prefers `GET /api/v1/sports` and falls back to this file.
 *
 * Generated from sports.py - do not hand-edit the rows.
 */

export interface SportCategory {
  slug: string;
  /** Bahasa Indonesia label. */
  label_id: string;
  /** English label. */
  label_en: string;
  /** Short editorial blurb (Bahasa Indonesia). */
  blurb: string;
  /** How many sports live in this category. */
  sport_count: number;
}

export interface Sport {
  slug: string;
  label_id: string;
  label_en: string;
  category: string;
}

export const SPORT_CATEGORIES: SportCategory[] = [
  { slug: "racket", label_id: "Raket", label_en: "Racket", blurb: "Padel, tenis, bulu tangkis, squash", sport_count: 8 },
  { slug: "team", label_id: "Bola & Tim", label_en: "Team", blurb: "Sepak bola, basket, voli, futsal", sport_count: 21 },
  { slug: "combat", label_id: "Bela Diri", label_en: "Combat", blurb: "Tinju, BJJ, judo, MMA, karate", sport_count: 19 },
  { slug: "strength", label_id: "Kekuatan", label_en: "Strength", blurb: "Angkat besi, powerlifting, crossfit", sport_count: 6 },
  { slug: "running", label_id: "Atletik & Lari", label_en: "Athletics & Running", blurb: "Lari, maraton, atletik", sport_count: 12 },
  { slug: "cycling", label_id: "Sepeda", label_en: "Cycling", blurb: "Sepeda jalan, gunung, BMX", sport_count: 5 },
  { slug: "water", label_id: "Air", label_en: "Water", blurb: "Renang, selancar, dayung, polo air", sport_count: 11 },
  { slug: "winter", label_id: "Es & Salju", label_en: "Winter & Ice", blurb: "Hoki es, ski, seluncur", sport_count: 7 },
  { slug: "precision", label_id: "Presisi", label_en: "Precision", blurb: "Golf, biliar, panahan, catur", sport_count: 9 },
  { slug: "gymnastics", label_id: "Senam", label_en: "Gymnastics", blurb: "Senam artistik, ritmik, trampolin", sport_count: 3 },
  { slug: "outdoor", label_id: "Panjat & Alam", label_en: "Climbing & Outdoor", blurb: "Panjat, bouldering, hiking", sport_count: 6 },
  { slug: "other", label_id: "Lainnya", label_en: "Other", blurb: "Olahraga lain yang diakui", sport_count: 4 },
];

export const SPORTS: Sport[] = [
  { slug: "padel", label_id: "Padel", label_en: "Padel", category: "racket" },
  { slug: "tennis", label_id: "Tenis", label_en: "Tennis", category: "racket" },
  { slug: "badminton", label_id: "Bulu Tangkis", label_en: "Badminton", category: "racket" },
  { slug: "table-tennis", label_id: "Tenis Meja", label_en: "Table Tennis", category: "racket" },
  { slug: "squash", label_id: "Squash", label_en: "Squash", category: "racket" },
  { slug: "pickleball", label_id: "Pickleball", label_en: "Pickleball", category: "racket" },
  { slug: "racquetball", label_id: "Racquetball", label_en: "Racquetball", category: "racket" },
  { slug: "beach-tennis", label_id: "Tenis Pantai", label_en: "Beach Tennis", category: "racket" },
  { slug: "football", label_id: "Sepak Bola", label_en: "Football", category: "team" },
  { slug: "futsal", label_id: "Futsal", label_en: "Futsal", category: "team" },
  { slug: "basketball", label_id: "Basket", label_en: "Basketball", category: "team" },
  { slug: "basketball-3x3", label_id: "Basket 3x3", label_en: "3x3 Basketball", category: "team" },
  { slug: "volleyball", label_id: "Bola Voli", label_en: "Volleyball", category: "team" },
  { slug: "beach-volleyball", label_id: "Voli Pantai", label_en: "Beach Volleyball", category: "team" },
  { slug: "handball", label_id: "Bola Tangan", label_en: "Handball", category: "team" },
  { slug: "rugby", label_id: "Rugby", label_en: "Rugby", category: "team" },
  { slug: "rugby-sevens", label_id: "Rugby Sevens", label_en: "Rugby Sevens", category: "team" },
  { slug: "american-football", label_id: "Sepak Bola Amerika", label_en: "American Football", category: "team" },
  { slug: "baseball", label_id: "Bisbol", label_en: "Baseball", category: "team" },
  { slug: "softball", label_id: "Sofbol", label_en: "Softball", category: "team" },
  { slug: "cricket", label_id: "Kriket", label_en: "Cricket", category: "team" },
  { slug: "hockey", label_id: "Hoki", label_en: "Hockey", category: "team" },
  { slug: "field-hockey", label_id: "Hoki Lapangan", label_en: "Field Hockey", category: "team" },
  { slug: "floorball", label_id: "Floorball", label_en: "Floorball", category: "team" },
  { slug: "netball", label_id: "Netball", label_en: "Netball", category: "team" },
  { slug: "ultimate-frisbee", label_id: "Ultimate Frisbee", label_en: "Ultimate Frisbee", category: "team" },
  { slug: "lacrosse", label_id: "Lakros", label_en: "Lacrosse", category: "team" },
  { slug: "dodgeball", label_id: "Dodgeball", label_en: "Dodgeball", category: "team" },
  { slug: "kabaddi", label_id: "Kabaddi", label_en: "Kabaddi", category: "team" },
  { slug: "boxing", label_id: "Tinju", label_en: "Boxing", category: "combat" },
  { slug: "kickboxing", label_id: "Kickboxing", label_en: "Kickboxing", category: "combat" },
  { slug: "muay-thai", label_id: "Muay Thai", label_en: "Muay Thai", category: "combat" },
  { slug: "mma", label_id: "MMA", label_en: "MMA", category: "combat" },
  { slug: "bjj", label_id: "Brazilian Jiu-Jitsu", label_en: "Brazilian Jiu-Jitsu", category: "combat" },
  { slug: "judo", label_id: "Judo", label_en: "Judo", category: "combat" },
  { slug: "karate", label_id: "Karate", label_en: "Karate", category: "combat" },
  { slug: "taekwondo", label_id: "Taekwondo", label_en: "Taekwondo", category: "combat" },
  { slug: "wrestling", label_id: "Gulat", label_en: "Wrestling", category: "combat" },
  { slug: "sambo", label_id: "Sambo", label_en: "Sambo", category: "combat" },
  { slug: "sanda", label_id: "Sanda", label_en: "Sanda", category: "combat" },
  { slug: "wushu", label_id: "Wushu", label_en: "Wushu", category: "combat" },
  { slug: "aikido", label_id: "Aikido", label_en: "Aikido", category: "combat" },
  { slug: "kendo", label_id: "Kendo", label_en: "Kendo", category: "combat" },
  { slug: "fencing", label_id: "Anggar", label_en: "Fencing", category: "combat" },
  { slug: "savate", label_id: "Savate", label_en: "Savate", category: "combat" },
  { slug: "krav-maga", label_id: "Krav Maga", label_en: "Krav Maga", category: "combat" },
  { slug: "pencak-silat", label_id: "Pencak Silat", label_en: "Pencak Silat", category: "combat" },
  { slug: "tarung-derajat", label_id: "Tarung Derajat", label_en: "Tarung Derajat", category: "combat" },
  { slug: "weightlifting", label_id: "Angkat Besi", label_en: "Weightlifting", category: "strength" },
  { slug: "powerlifting", label_id: "Powerlifting", label_en: "Powerlifting", category: "strength" },
  { slug: "bodybuilding", label_id: "Binaraga", label_en: "Bodybuilding", category: "strength" },
  { slug: "crossfit", label_id: "CrossFit", label_en: "CrossFit", category: "strength" },
  { slug: "strongman", label_id: "Strongman", label_en: "Strongman", category: "strength" },
  { slug: "calisthenics", label_id: "Calisthenics", label_en: "Calisthenics", category: "strength" },
  { slug: "running", label_id: "Lari", label_en: "Running", category: "running" },
  { slug: "sprinting", label_id: "Lari Cepat", label_en: "Sprinting", category: "running" },
  { slug: "marathon", label_id: "Maraton", label_en: "Marathon", category: "running" },
  { slug: "half-marathon", label_id: "Half Marathon", label_en: "Half Marathon", category: "running" },
  { slug: "trail-running", label_id: "Trail Running", label_en: "Trail Running", category: "running" },
  { slug: "track-field", label_id: "Atletik", label_en: "Track & Field", category: "running" },
  { slug: "long-jump", label_id: "Lompat Jauh", label_en: "Long Jump", category: "running" },
  { slug: "high-jump", label_id: "Lompat Tinggi", label_en: "High Jump", category: "running" },
  { slug: "pole-vault", label_id: "Lompat Galah", label_en: "Pole Vault", category: "running" },
  { slug: "shot-put", label_id: "Tolak Peluru", label_en: "Shot Put", category: "running" },
  { slug: "discus", label_id: "Lempar Cakram", label_en: "Discus", category: "running" },
  { slug: "javelin", label_id: "Lempar Lembing", label_en: "Javelin", category: "running" },
  { slug: "road-cycling", label_id: "Sepeda Jalan", label_en: "Road Cycling", category: "cycling" },
  { slug: "mountain-biking", label_id: "Sepeda Gunung", label_en: "Mountain Biking", category: "cycling" },
  { slug: "bmx", label_id: "BMX", label_en: "BMX", category: "cycling" },
  { slug: "track-cycling", label_id: "Sepeda Trek", label_en: "Track Cycling", category: "cycling" },
  { slug: "gravel-cycling", label_id: "Sepeda Gravel", label_en: "Gravel Cycling", category: "cycling" },
  { slug: "swimming", label_id: "Renang", label_en: "Swimming", category: "water" },
  { slug: "diving", label_id: "Loncat Indah", label_en: "Diving", category: "water" },
  { slug: "open-water-swimming", label_id: "Renang Perairan Terbuka", label_en: "Open Water Swimming", category: "water" },
  { slug: "surfing", label_id: "Selancar", label_en: "Surfing", category: "water" },
  { slug: "windsurfing", label_id: "Windsurfing", label_en: "Windsurfing", category: "water" },
  { slug: "sailing", label_id: "Berlayar", label_en: "Sailing", category: "water" },
  { slug: "kayaking", label_id: "Kayak", label_en: "Kayaking", category: "water" },
  { slug: "canoeing", label_id: "Kano", label_en: "Canoeing", category: "water" },
  { slug: "rowing", label_id: "Dayung", label_en: "Rowing", category: "water" },
  { slug: "rafting", label_id: "Arung Jeram", label_en: "Rafting", category: "water" },
  { slug: "water-polo", label_id: "Polo Air", label_en: "Water Polo", category: "water" },
  { slug: "ice-hockey", label_id: "Hoki Es", label_en: "Ice Hockey", category: "winter" },
  { slug: "figure-skating", label_id: "Seluncur Indah", label_en: "Figure Skating", category: "winter" },
  { slug: "speed-skating", label_id: "Seluncur Cepat", label_en: "Speed Skating", category: "winter" },
  { slug: "short-track", label_id: "Short Track", label_en: "Short Track", category: "winter" },
  { slug: "curling", label_id: "Curling", label_en: "Curling", category: "winter" },
  { slug: "skiing", label_id: "Ski", label_en: "Skiing", category: "winter" },
  { slug: "snowboarding", label_id: "Snowboard", label_en: "Snowboarding", category: "winter" },
  { slug: "golf", label_id: "Golf", label_en: "Golf", category: "precision" },
  { slug: "bowling", label_id: "Boling", label_en: "Bowling", category: "precision" },
  { slug: "billiards", label_id: "Biliar", label_en: "Billiards", category: "precision" },
  { slug: "pool", label_id: "Pool", label_en: "Pool", category: "precision" },
  { slug: "snooker", label_id: "Snooker", label_en: "Snooker", category: "precision" },
  { slug: "darts", label_id: "Panah Sasar", label_en: "Darts", category: "precision" },
  { slug: "archery", label_id: "Panahan", label_en: "Archery", category: "precision" },
  { slug: "shooting", label_id: "Menembak", label_en: "Shooting Sports", category: "precision" },
  { slug: "chess", label_id: "Catur", label_en: "Chess", category: "precision" },
  { slug: "artistic-gymnastics", label_id: "Senam Artistik", label_en: "Artistic Gymnastics", category: "gymnastics" },
  { slug: "rhythmic-gymnastics", label_id: "Senam Ritmik", label_en: "Rhythmic Gymnastics", category: "gymnastics" },
  { slug: "trampoline", label_id: "Trampolin", label_en: "Trampoline", category: "gymnastics" },
  { slug: "sport-climbing", label_id: "Panjat Sport", label_en: "Sport Climbing", category: "outdoor" },
  { slug: "bouldering", label_id: "Bouldering", label_en: "Bouldering", category: "outdoor" },
  { slug: "rock-climbing", label_id: "Panjat Tebing", label_en: "Rock Climbing", category: "outdoor" },
  { slug: "mountaineering", label_id: "Pendakian Gunung", label_en: "Mountaineering", category: "outdoor" },
  { slug: "hiking", label_id: "Hiking", label_en: "Hiking", category: "outdoor" },
  { slug: "trekking", label_id: "Trekking", label_en: "Trekking", category: "outdoor" },
  { slug: "sepak-takraw", label_id: "Sepak Takraw", label_en: "Sepak Takraw", category: "other" },
  { slug: "equestrian", label_id: "Berkuda", label_en: "Equestrian", category: "other" },
  { slug: "skateboarding", label_id: "Skateboard", label_en: "Skateboarding", category: "other" },
  { slug: "roller-skating", label_id: "Sepatu Roda", label_en: "Roller Skating", category: "other" },
];

/** slug -> category slug, for fast lookups. */
export const SPORT_CATEGORY_OF: Record<string, string> = Object.fromEntries(
  SPORTS.map((s) => [s.slug, s.category]),
);

/** Sports grouped by their category slug. */
export const SPORTS_BY_CATEGORY: Record<string, Sport[]> = Object.fromEntries(
  SPORT_CATEGORIES.map((c) => [c.slug, SPORTS.filter((s) => s.category === c.slug)]),
);

/** Look up a sport by slug. */
export function sportBySlug(slug: string | null | undefined): Sport | undefined {
  if (!slug) return undefined;
  return SPORTS.find((s) => s.slug === slug);
}

