import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

/** Filter/status chip. Interactive ones are real <button>s. */
export function Chip({
  active,
  children,
  className,
  ...rest
}: {
  active?: boolean;
  children: ReactNode;
  className?: string;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      aria-pressed={active}
      className={cn(
        'inline-flex min-h-[36px] shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-3.5 text-sm font-semibold transition-all duration-200',
        active
          ? 'border-ink bg-ink text-ink-inv'
          : 'border-line bg-surface text-ink-2 hover:border-ink/25 hover:text-ink',
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
