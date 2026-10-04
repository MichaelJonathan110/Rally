/**
 * RALLY string layer (Phase 2).
 *
 * One tiny dictionary so every user-facing string on the pages we touch is
 * switchable between Bahasa Indonesia (id, default) and English (en).
 * Phase 3 only needs to fill the en column - the plumbing is already here.
 *
 * Usage:
 *   import { t, useT } from '@/i18n/strings';
 *   t('hero.ctaExplore')     // outside React (reads current lang)
 *   const t = useT();        // reactive inside React
 *
 * The active language lives in localStorage under rally.lang.
 */
import { create } from 'zustand';

export type Lang = 'id' | 'en';

const LANG_KEY = 'rally.lang';

/** The dictionary. `id` is the source of truth for the key set. */
export const STRINGS = {
  id: {
    'common.allCities': 'Semua kota',
    'common.all': 'Semua',
    'common.reset': 'Reset filter',
    'common.loading': 'Memuat...',
    'cat.racket': 'Raket',
    'cat.team': 'Bola & Tim',
    'cat.combat': 'Bela Diri',
    'cat.strength': 'Kekuatan',
    'cat.running': 'Atletik & Lari',
    'cat.cycling': 'Sepeda',
    'cat.water': 'Air',
    'cat.winter': 'Es & Salju',
    'cat.precision': 'Presisi',
    'cat.gymnastics': 'Senam',
    'cat.outdoor': 'Panjat & Alam',
    'cat.other': 'Lainnya',

    'nav.search': 'Cari kegiatan, venue, komunitas',

    'city.label': 'Kota',
    'city.choose': 'Pilih kotamu',
    'city.showing': 'Menampilkan kegiatan di',
    'city.showingAll': 'Menampilkan semua kota',
    'city.change': 'Ganti kota',
    'city.seeAll': 'Lihat semua kota',
    'city.selectAria': 'Pilih kota',
    'city.listAria': 'Daftar kota',
    'city.loading': 'Memuat kota...',
    'city.countActivities': '{count} kegiatan',

    'hero.eyebrow': 'Dunia kegiatan, bukan dasbor',
    'hero.titleGuest1': 'Temukan',
    'hero.titleGuest2': 'komunitasmu.',
    'hero.subtitleA': 'Olahraga bareng, cari teman selevel, dan naikkan MMR-mu di',
    'hero.subtitleB': 'kegiatan nyata di seluruh Indonesia.',
    'hero.ctaExplore': 'Mulai jelajah',
    'hero.ctaCreate': 'Buat kegiatan',
    'hero.ctaJoin': 'Gabung gratis',
    'hero.statActivities': 'Kegiatan aktif',
    'hero.statCategories': 'Kategori',
    'hero.mmrUp': 'MMR naik minggu ini',
    'hero.mmrBadgeAlt': 'Lencana MMR RALLY - trofi peringkat Elo',

    'type.title': 'Jenis kegiatan',
    'type.all': 'Semua jenis',
    'type.filterHint': 'Filter jenis kegiatan',
    'type.none': 'Belum ada jenis untuk kategori ini',

    'discover.eyebrow': 'Jelajah',
    'discover.title': 'Temukan kegiatan berikutnya',
    'discover.subtitle': 'Cari kegiatan, venue, atau komunitas di seluruh Indonesia.',
    'discover.searchPlaceholder': 'Cari kegiatan, kota, atau kata kunci...',
    'discover.searchLabel': 'Cari kegiatan',
    'discover.level': 'Level',
    'discover.sort': 'Urutkan',
    'discover.sortSoonest': 'Paling cepat',
    'discover.sortCheapest': 'Paling murah',
    'discover.sortPopular': 'Paling ramai',
    'discover.found': '{count} kegiatan ditemukan',
    'discover.foundLabel': 'kegiatan ditemukan',
    'discover.prev': 'Sebelumnya',
    'discover.next': 'Berikutnya',
    'discover.page': 'Halaman {page} dari {total}',
    'discover.emptyTitle': 'Tidak ada kegiatan cocok',
    'discover.emptyDesc': 'Coba perluas filter atau gunakan kata kunci lain.',
    'discover.errorTitle': 'Gagal memuat kegiatan',
    'discover.scopedTo': 'Kegiatan di {city}',

    'mmr.emptyTitle': 'Belum ada peringkat',
    'mmr.emptyDesc': 'Ikut kegiatan ber-MMR dan selesaikan pertandingan untuk membuka peringkatmu.',
    'mmr.panelTitle': 'Peringkat MMR',
    'mmr.noRank': 'Belum ada peringkat',
  },
  en: {
    'common.allCities': 'All cities',
    'common.all': 'All',
    'common.reset': 'Reset filters',
    'common.loading': 'Loading...',
    'cat.racket': 'Racket',
    'cat.team': 'Team',
    'cat.combat': 'Combat',
    'cat.strength': 'Strength',
    'cat.running': 'Athletics & Running',
    'cat.cycling': 'Cycling',
    'cat.water': 'Water',
    'cat.winter': 'Winter & Ice',
    'cat.precision': 'Precision',
    'cat.gymnastics': 'Gymnastics',
    'cat.outdoor': 'Climbing & Outdoor',
    'cat.other': 'Other',

    'nav.search': 'Search activities, venues, communities',

    'city.label': 'City',
    'city.choose': 'Pick your city',
    'city.showing': 'Showing activities in',
    'city.showingAll': 'Showing all cities',
    'city.change': 'Change city',
    'city.seeAll': 'See all cities',
    'city.selectAria': 'Choose city',
    'city.listAria': 'City list',
    'city.loading': 'Loading cities...',
    'city.countActivities': '{count} activities',

    'hero.eyebrow': 'A world of activities, not a dashboard',
    'hero.titleGuest1': 'Find your',
    'hero.titleGuest2': 'community.',
    'hero.subtitleA': 'Play together, find people at your level, and grow your MMR across',
    'hero.subtitleB': 'real activities all over Indonesia.',
    'hero.ctaExplore': 'Start exploring',
    'hero.ctaCreate': 'Create activity',
    'hero.ctaJoin': 'Join free',
    'hero.statActivities': 'Active activities',
    'hero.statCategories': 'Categories',
    'hero.mmrUp': 'MMR up this week',
    'hero.mmrBadgeAlt': 'RALLY MMR badge - an Elo rank trophy',

    'type.title': 'Activity type',
    'type.all': 'All types',
    'type.filterHint': 'Filter by activity type',
    'type.none': 'No types for this category yet',

    'discover.eyebrow': 'Discover',
    'discover.title': 'Find your next activity',
    'discover.subtitle': 'Search activities, venues, or communities across Indonesia.',
    'discover.searchPlaceholder': 'Search activities, cities, or keywords...',
    'discover.searchLabel': 'Search activities',
    'discover.level': 'Level',
    'discover.sort': 'Sort',
    'discover.sortSoonest': 'Soonest',
    'discover.sortCheapest': 'Cheapest',
    'discover.sortPopular': 'Most popular',
    'discover.found': '{count} activities found',
    'discover.foundLabel': 'activities found',
    'discover.prev': 'Previous',
    'discover.next': 'Next',
    'discover.page': 'Page {page} of {total}',
    'discover.emptyTitle': 'No matching activities',
    'discover.emptyDesc': 'Try widening your filters or using another keyword.',
    'discover.errorTitle': 'Failed to load activities',
    'discover.scopedTo': 'Activities in {city}',

    'mmr.emptyTitle': 'No ranking yet',
    'mmr.emptyDesc': 'Join MMR activities and finish matches to unlock your ranking.',
    'mmr.panelTitle': 'MMR ranking',
    'mmr.noRank': 'No ranking yet',
  },
} as const;

export type StringKey = keyof typeof STRINGS['id'];

function readLang(): Lang {
  try {
    const v = typeof localStorage !== 'undefined' ? localStorage.getItem(LANG_KEY) : null;
    return v === 'en' ? 'en' : 'id';
  } catch {
    return 'id';
  }
}

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
}

export const useLangStore = create<LangState>((set) => ({
  lang: readLang(),
  setLang: (lang) => {
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch {
      /* storage unavailable - language still applies for this session */
    }
    set({ lang });
  },
}));

export function getLang(): Lang {
  return useLangStore.getState().lang;
}

export function setLang(lang: Lang): void {
  useLangStore.getState().setLang(lang);
}

function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_m, k: string) => (k in vars ? String(vars[k]) : '{' + k + '}'));
}

function translate(lang: Lang, key: StringKey, vars?: Record<string, string | number>): string {
  const table = STRINGS[lang] as Record<string, string>;
  const fallback = STRINGS.id as Record<string, string>;
  const value = table[key] ?? fallback[key] ?? key;
  return interpolate(value, vars);
}

/** Non-reactive translate using the current language (module scope / handlers). */
export function t(key: StringKey, vars?: Record<string, string | number>): string {
  return translate(getLang(), key, vars);
}

/** Reactive translate hook - re-renders the component when the language changes. */
export function useT(): (key: StringKey, vars?: Record<string, string | number>) => string {
  const lang = useLangStore((s) => s.lang);
  return (key, vars) => translate(lang, key, vars);
}

export default STRINGS;
