/**
 * CATEGORY IDENTITY - the visual language of RALLY.
 *
 * Every activity category owns a pastel tone, a Bahasa Indonesia label and a
 * cover photograph of real people doing the thing. The tone drives card
 * surfaces, chips, data viz and the interactive category object, so a page
 * never renders "12 identical cards".
 */
import type { ActivityCategory } from '@/api/types';

export type Tone = 'cyan' | 'mint' | 'lime' | 'yellow' | 'coral' | 'neutral';

export interface CategoryMeta {
  id: ActivityCategory;
  /** Bahasa Indonesia label shown in the UI. */
  label: string;
  /** Short editorial blurb for headers. */
  blurb: string;
  tone: Tone;
  emoji: string;
}

export const CATEGORIES: CategoryMeta[] = [
  { id: 'racket', label: 'Raket', blurb: 'Padel, tenis, bulu tangkis, squash', tone: 'cyan', emoji: '🏸' },
  { id: 'team', label: 'Bola & Tim', blurb: 'Sepak bola, basket, voli, futsal', tone: 'lime', emoji: '⚽' },
  { id: 'combat', label: 'Bela Diri', blurb: 'Tinju, BJJ, judo, MMA, karate', tone: 'coral', emoji: '🥊' },
  { id: 'strength', label: 'Kekuatan', blurb: 'Angkat besi, powerlifting, crossfit', tone: 'yellow', emoji: '🏋️' },
  { id: 'running', label: 'Atletik & Lari', blurb: 'Lari, maraton, atletik', tone: 'mint', emoji: '🏃' },
  { id: 'cycling', label: 'Sepeda', blurb: 'Sepeda jalan, gunung, BMX', tone: 'neutral', emoji: '🚴' },
  { id: 'water', label: 'Air', blurb: 'Renang, selancar, dayung, polo air', tone: 'cyan', emoji: '🏊' },
  { id: 'winter', label: 'Es & Salju', blurb: 'Hoki es, ski, seluncur', tone: 'mint', emoji: '⛷️' },
  { id: 'precision', label: 'Presisi', blurb: 'Golf, biliar, panahan, catur', tone: 'yellow', emoji: '🎯' },
  { id: 'gymnastics', label: 'Senam', blurb: 'Senam artistik, ritmik, trampolin', tone: 'coral', emoji: '🤸' },
  { id: 'outdoor', label: 'Panjat & Alam', blurb: 'Panjat, bouldering, hiking', tone: 'lime', emoji: '🧗' },
  { id: 'other', label: 'Lainnya', blurb: 'Olahraga lain yang diakui', tone: 'neutral', emoji: '🏅' },
];

export const CATEGORY_MAP: Record<string, CategoryMeta> = Object.fromEntries(
  CATEGORIES.map((c) => [c.id, c]),
);

export function categoryMeta(id: string | null | undefined): CategoryMeta {
  return CATEGORY_MAP[id ?? 'other'] ?? CATEGORY_MAP.other;
}

export interface ToneStyle {
  /** Solid pastel fill (chips, tiles). */
  solid: string;
  /** Very soft pastel wash (card headers, insets). */
  soft: string;
  /** Text colour that stays legible on the pastel. */
  text: string;
  /** Border tint. */
  border: string;
  /** Raw hex, for inline gradients / SVG fills. */
  hex: string;
  /** Light gradient used as the graceful image fallback. */
  gradient: string;
}

export const TONE: Record<Tone, ToneStyle> = {
  cyan: {
    solid: 'bg-cyan',
    soft: 'bg-cyan-soft',
    text: 'text-ink',
    border: 'border-cyan',
    hex: '#9FE3DC',
    gradient: 'linear-gradient(135deg,#E4F6F3 0%,#9FE3DC 100%)',
  },
  mint: {
    solid: 'bg-mint',
    soft: 'bg-mint-soft',
    text: 'text-ink',
    border: 'border-mint',
    hex: '#B9E9C9',
    gradient: 'linear-gradient(135deg,#E9F8EF 0%,#B9E9C9 100%)',
  },
  lime: {
    solid: 'bg-lime',
    soft: 'bg-lime-soft',
    text: 'text-ink',
    border: 'border-lime',
    hex: '#D9F08C',
    gradient: 'linear-gradient(135deg,#F2FADF 0%,#D9F08C 100%)',
  },
  yellow: {
    solid: 'bg-yellow',
    soft: 'bg-yellow-soft',
    text: 'text-ink',
    border: 'border-yellow',
    hex: '#FFE28A',
    gradient: 'linear-gradient(135deg,#FFF8DE 0%,#FFE28A 100%)',
  },
  coral: {
    solid: 'bg-coral',
    soft: 'bg-coral-soft',
    text: 'text-ink',
    border: 'border-coral',
    hex: '#FF9C86',
    gradient: 'linear-gradient(135deg,#FFE9E2 0%,#FF9C86 100%)',
  },
  neutral: {
    solid: 'bg-paper-warm',
    soft: 'bg-surface-muted',
    text: 'text-ink',
    border: 'border-line',
    hex: '#E8E0D4',
    gradient: 'linear-gradient(135deg,#F6F1E8 0%,#E3D9C8 100%)',
  },
};

export const SKILL_LABEL: Record<string, string> = {
  beginner: 'Pemula',
  intermediate: 'Menengah',
  advanced: 'Mahir',
  expert: 'Expert',
  any: 'Semua level',
};

export function skillLabel(v: string | null | undefined): string {
  return SKILL_LABEL[v ?? 'any'] ?? 'Semua level';
}
