import { cn } from '@/lib/utils';

const UNRANKED = { min: -1, label: 'Unranked' } as const;

const TIERS = [
  { min: 2400, label: 'God' },
  { min: 2200, label: 'Grandmaster' },
  { min: 2000, label: 'Master' },
  { min: 1800, label: 'Diamond' },
  { min: 1600, label: 'Platinum' },
  { min: 1400, label: 'Gold' },
  { min: 1200, label: 'Silver' },
  { min: 600, label: 'Bronze' },
] as const;

export type RankTier = (typeof TIERS)[number]['label'];

export function tierFor(rating: number | null | undefined) {
  // Guard FIRST: a missing or non-positive MMR is never a tier.
  if (rating === null || rating === undefined || !Number.isFinite(rating) || rating <= 0) {
    return UNRANKED;
  }
  return TIERS.find((t) => rating >= t.min) ?? TIERS[TIERS.length - 1];
}

const TONE: Record<string, string> = {
  Unranked: 'bg-surface-muted text-ink',
  God: 'bg-yellow text-ink',
  Grandmaster: 'bg-coral text-ink',
  Master: 'bg-violet text-ink',
  Diamond: 'bg-cyan text-ink',
  Platinum: 'bg-mint text-ink',
  Gold: 'bg-yellow text-ink',
  Silver: 'bg-surface-muted text-ink',
  Bronze: 'bg-coral-soft text-ink',
};

export function RankBadge({ rating, className, showRating = true }: { rating: number | null | undefined; className?: string; showRating?: boolean }) {
  const tier = tierFor(rating);
  const isUnranked = tier.label === 'Unranked';
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border border-ink/10 px-2.5 py-1 text-xs font-semibold', TONE[tier.label] ?? 'bg-surface-muted text-ink', className)}>
      <span aria-hidden>{'\u25c6'}</span>
      {tier.label}
      {showRating && !isUnranked ? <span className='font-mono text-[11px] tabular-nums opacity-80'>{Math.round(rating as number)}</span> : null}
    </span>
  );
}
