/**
 * BRAND CONFIG — single swappable source of truth (frontend).
 * Read from Vite env at build time; safe defaults keep the app runnable
 * with zero configuration. Rebrand by changing env vars or these defaults.
 */
export interface Brand {
  name: string;
  tagline: string;
  shortName: string;
  domain: string;
  supportEmail: string;
  theme: { primary: string; accent: string; radius: string };
  social: { twitter: string; instagram: string; discord: string };
}

function env(key: string, fallback: string): string {
  const v = (import.meta.env as Record<string, string | undefined>)[key];
  return v && v.length > 0 ? v : fallback;
}

export const brand: Brand = {
  name: env('VITE_BRAND_NAME', 'RALLY'),
  tagline: env('VITE_BRAND_TAGLINE', 'Find your people. Do more together.'),
  shortName: env('VITE_BRAND_SHORT_NAME', 'RALLY'),
  domain: env('VITE_BRAND_DOMAIN', 'rally.example'),
  supportEmail: env('VITE_BRAND_SUPPORT_EMAIL', 'support@rally.example'),
  theme: {
    primary: env('VITE_BRAND_PRIMARY', '#6366f1'),
    accent: env('VITE_BRAND_ACCENT', '#22d3ee'),
    radius: env('VITE_BRAND_RADIUS', '0.75rem'),
  },
  social: {
    twitter: env('VITE_BRAND_TWITTER', ''),
    instagram: env('VITE_BRAND_INSTAGRAM', ''),
    discord: env('VITE_BRAND_DISCORD', ''),
  },
};

export default brand;
