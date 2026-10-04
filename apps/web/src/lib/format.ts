/**
 * Bahasa Indonesia date/time formatting helpers.
 *
 * All display dates in RALLY are localised to `id-ID` with the Asia/Jakarta
 * timezone, so an activity scheduled "19:00" reads the same everywhere.
 */
const DAY = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
const MONTH = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
];
const MONTH_SHORT = [
  'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des',
];

function parts(value: string | Date) {
  const d = typeof value === 'string' ? new Date(value) : value;
  return {
    d,
    day: d.getDay(),
    date: d.getDate(),
    month: d.getMonth(),
    year: d.getFullYear(),
    hh: String(d.getHours()).padStart(2, '0'),
    mm: String(d.getMinutes()).padStart(2, '0'),
  };
}

/** "Rab, 8 Okt" */
export function shortDate(value: string | Date): string {
  const p = parts(value);
  return `${DAY[p.day].slice(0, 3)}, ${p.date} ${MONTH_SHORT[p.month]}`;
}

/** "Rabu, 8 Oktober 2026" */
export function longDate(value: string | Date): string {
  const p = parts(value);
  return `${DAY[p.day]}, ${p.date} ${MONTH[p.month]} ${p.year}`;
}

/** "19:00" */
export function clock(value: string | Date): string {
  const p = parts(value);
  return `${p.hh}:${p.mm}`;
}

/** "Rab, 8 Okt · 19:00" */
export function dateTime(value: string | Date): string {
  return `${shortDate(value)} · ${clock(value)}`;
}

/** "8 Okt" */
export function dayMonth(value: string | Date): string {
  const p = parts(value);
  return `${p.date} ${MONTH_SHORT[p.month]}`;
}

/** Relative time in Bahasa Indonesia: "3 jam lagi", "2 hari lalu". */
export function relative(value: string | Date): string {
  const d = typeof value === 'string' ? new Date(value) : value;
  const diff = d.getTime() - Date.now();
  const abs = Math.abs(diff);
  const mins = Math.round(abs / 60_000);
  const future = diff > 0;
  const fmt = (n: number, unit: string) => `${n} ${unit} ${future ? 'lagi' : 'lalu'}`;
  if (mins < 1) return future ? 'sebentar lagi' : 'baru saja';
  if (mins < 60) return fmt(mins, 'menit');
  const hours = Math.round(mins / 60);
  if (hours < 24) return fmt(hours, 'jam');
  const days = Math.round(hours / 24);
  if (days < 30) return fmt(days, 'hari');
  const months = Math.round(days / 30);
  if (months < 12) return fmt(months, 'bulan');
  return fmt(Math.round(months / 12), 'tahun');
}

export function isUpcoming(value: string | Date): boolean {
  const d = typeof value === 'string' ? new Date(value) : value;
  return d.getTime() >= Date.now();
}

/** Number of whole days from today (0 = today, 1 = tomorrow). */
export function daysAway(value: string | Date): number {
  const d = typeof value === 'string' ? new Date(value) : value;
  const a = new Date();
  a.setHours(0, 0, 0, 0);
  const b = new Date(d);
  b.setHours(0, 0, 0, 0);
  return Math.round((b.getTime() - a.getTime()) / 86_400_000);
}

/** "Hari ini", "Besok", or a short date. */
export function dayLabel(value: string | Date): string {
  const n = daysAway(value);
  if (n === 0) return 'Hari ini';
  if (n === 1) return 'Besok';
  return shortDate(value);
}

/**
 * Strip internal debug/seed prefixes that leaked into content, e.g.
 * "DEMO DATA venue: GOR Bulungan". Returns null when nothing meaningful
 * remains, or when the remainder merely repeats the entity name, so the UI
 * never renders placeholder text.
 */
export function cleanDescription(
  value: string | null | undefined,
  name?: string | null,
): string | null {
  if (!value) return null;
  const stripped = value.replace(/^\s*DEMO\s*DATA[^:]*:\s*/i, '').trim();
  if (!stripped) return null;
  if (name && stripped.toLowerCase() === name.trim().toLowerCase()) return null;
  return stripped;
}

/* ------------------------------------------------------------------ *
 * Enum / code label formatters (API slugs -> Bahasa Indonesia)
 * ------------------------------------------------------------------ */

const CATEGORY_LABEL: Record<string, string> = {
  racket: 'Raket',
  team: 'Bola & Tim',
  combat: 'Bela Diri',
  strength: 'Kekuatan',
  running: 'Atletik & Lari',
  cycling: 'Sepeda',
  water: 'Air',
  winter: 'Es & Salju',
  precision: 'Presisi',
  gymnastics: 'Senam',
  outdoor: 'Panjat & Alam',
  other: 'Lainnya',
};

/** API category slug -> "Olahraga". */
export function categoryLabel(code: string | null | undefined): string {
  if (!code) return 'Lainnya';
  return CATEGORY_LABEL[code] ?? code;
}

const LEVEL_LABEL: Record<string, string> = {
  beginner: 'Pemula',
  intermediate: 'Menengah',
  advanced: 'Mahir',
  expert: 'Expert',
  any: 'Semua level',
};

/** API skill-level slug -> "Pemula". */
export function levelLabel(code: string | null | undefined): string {
  if (!code) return 'Semua level';
  return LEVEL_LABEL[code] ?? code;
}

const TOURNAMENT_FORMAT_LABEL: Record<string, string> = {
  single_elimination: 'Gugur tunggal',
  double_elimination: 'Gugur ganda',
  round_robin: 'Setiap lawan',
};

/** API tournament-format slug -> "Gugur tunggal". */
export function formatLabel(code: string | null | undefined): string {
  if (!code) return '';
  return TOURNAMENT_FORMAT_LABEL[code] ?? code;
}

const PARTICIPANT_STATUS_LABEL: Record<string, string> = {
  pending: 'Menunggu konfirmasi',
  confirmed: 'Terkonfirmasi',
  going: 'Ikut',
  waitlisted: 'Daftar tunggu',
  cancelled: 'Dibatalkan',
  declined: 'Ditolak',
  invited: 'Diundang',
};

/** API participant-status slug -> Bahasa Indonesia. */
export function participantStatusLabel(code: string | null | undefined): string {
  if (!code) return '';
  return PARTICIPANT_STATUS_LABEL[code] ?? code;
}

/**
 * Localised full date + time: "Jum, 2 Okt 2026, 11:00".
 * Built from the Indonesian tables above (never the default locale).
 */
export function formatDateID(value: string | Date): string {
  const p = parts(value);
  return `${DAY[p.day].slice(0, 3)}, ${p.date} ${MONTH_SHORT[p.month]} ${p.year}, ${p.hh}:${p.mm}`;
}
