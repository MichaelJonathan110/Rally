import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/**
 * Editorial page header. Large display type on the left, an optional action on
 * the right - the same rhythm on every page so the app reads as one product.
 */
export function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
  className,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        'flex flex-wrap items-end justify-between gap-x-6 gap-y-4 border-b border-line pb-5',
        className,
      )}
    >
      <div className="min-w-0 max-w-2xl">
        {eyebrow ? <p className="eyebrow mb-2">{eyebrow}</p> : null}
        <h1 className="text-balance font-display text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">
          {title}
        </h1>
        {subtitle ? <p className="mt-2 text-sm text-ink-2 sm:text-base">{subtitle}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}
