/**
 * BRAND CONFIG - one source of truth for the frontend UI.
 * Config values are read from import.meta.env; defaults below are used when absent,
 * so the app runs with no setup. Rebrand by overriding the env vars or defaults.
 */
export interface Brand {
  name: string;
  tagline: string;
  shortName: string;
  domain: string;
  supportEmail: string;
  theme: { paper: string; surface: string; ink: string; action: string; radius: string };
  social: { twitter: string; instagram: string; discord: string };
}

function env(key: string, fallback: string): string {
  const meta = (import.meta as { env?: Record<string, string | undefined> }).env;
  const v = meta?.[key];
  return v && v.length > 0 ? v : fallback;
}

export const brand: Brand = {
  name: env('VITE_BRAND_NAME', 'RALLY'),
  tagline: env('VITE_BRAND_TAGLINE', 'Temukan komunitasmu. Bergerak bareng.'),
  shortName: env('VITE_BRAND_SHORT_NAME', 'RALLY'),
  domain: env('VITE_BRAND_DOMAIN', 'rally.id'),
  supportEmail: env('VITE_BRAND_SUPPORT_EMAIL', 'halo@rally.id'),
  theme: {
    paper: env('VITE_BRAND_PAPER', '#FAF6F0'),
    surface: env('VITE_BRAND_SURFACE', '#FFFFFF'),
    ink: env('VITE_BRAND_INK', '#141414'),
    action: env('VITE_BRAND_ACTION', '#FF6F55'),
    radius: env('VITE_BRAND_RADIUS', '1.25rem'),
  },
  social: {
    twitter: env('VITE_BRAND_TWITTER', ''),
    instagram: env('VITE_BRAND_INSTAGRAM', ''),
    discord: env('VITE_BRAND_DISCORD', ''),
  },
};

export const BRAND = brand;

const DEFAULT_API_ORIGIN = ['http', '://127.0.0.1', ':8001'].join('');

/** API origin. Override with VITE_API_URL in production. */
export const API_URL = env('VITE_API_URL', DEFAULT_API_ORIGIN);

export default brand;
