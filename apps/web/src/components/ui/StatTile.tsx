import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { TONE, type Tone } from '@/config/categories';

/**
 * Statistic tile.
 *
 * The value is rendered directly (never animated from 0) so a real count is
 * always visible immediately - including below the fold and in screenshots -
 * instead of a misleading "0" that only resolves once scrolled into view.
 */
export function StatTile({
  label,
  value,
  suffix,
  hint,
  tone = 'neutral',
  icon,
  format,
  className,
}: {
  label: string;
  value: number;
  suffix?: string;
  hint?: string;
  tone?: Tone;
  icon?: ReactNode;
  format?: (n: number) => string;
  className?: string;
}) {
  const t = TONE[tone];
  const text = format ? format(value) : Math.round(value).toLocaleString('id-ID');
  return (
    <div className={cn('rounded-lg border border-line bg-surface p-4 shadow-soft', className)}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-2xs font-semibold uppercase tracking-[0.14em] text-ink-3">
          {label}
        </span>
        {icon ? (
          <span
            className={cn('grid h-7 w-7 place-items-center rounded-md text-ink', t.solid)}
            aria-hidden
          >
            {icon}
          </span>
        ) : null}
      </div>
      <p className="mt-2 font-display text-3xl font-extrabold tracking-tight text-ink tabular-nums">
        {text}
        {suffix ? <span className="ml-0.5 text-lg text-ink-2">{suffix}</span> : null}
      </p>
      {hint ? <p className="mt-1 text-xs text-ink-3">{hint}</p> : null}
    </div>
  );
}
