import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('card p-4 sm:p-5', className)} {...rest} />;
}

export function CardHeader({ title, subtitle, action, className }: {
  title: ReactNode;
  subtitle?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('mb-3 flex items-start justify-between gap-3', className)}>
      <div className="min-w-0">
        <h3 className="truncate text-base font-semibold text-ink">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-sm text-ink-3">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}
