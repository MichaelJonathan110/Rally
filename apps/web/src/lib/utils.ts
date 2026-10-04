import clsx, { type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

/**
 * Format an activity/booking price for display.
 *
 * RALLY stores money as an integer "minor unit" value. For IDR (the primary
 * currency) the minor unit IS the rupiah - there are no sen in practice - so
 * the stored integer is the full amount and is rendered with no decimals,
 * e.g. 75000 -> "Rp 75.000". A zero amount is shown as "Gratis" (free), which
 * is how Indonesian event listings phrase it. Other currencies fall back to a
 * standard Intl currency format over 100 minor units.
 */
export function formatCents(cents: number, currency = 'IDR'): string {
  if (!Number.isFinite(cents)) return '';
  if (cents === 0) return 'Gratis';
  if (currency === 'IDR') {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0,
    }).format(cents);
  }
  return new Intl.NumberFormat('id-ID', { style: 'currency', currency }).format(cents / 100);
}

/** True when the price should read as free. */
export function isFree(cents: number | null | undefined): boolean {
  return !cents;
}

export function initials(name: string | undefined | null): string {
  if (!name) return '?';
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}

export function titleCase(value: string): string {
  return value.replace(/[_-]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function toIso(value: string | Date): string {
  return value instanceof Date ? value.toISOString() : new Date(value).toISOString();
}
