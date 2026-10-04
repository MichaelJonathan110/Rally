import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface TabItem {
  id?: string;
  value?: string;
  label: string;
  badge?: number;
}

export function Tabs({
  items,
  value,
  onChange,
  className,
}: {
  items: TabItem[];
  value: string;
  onChange: (id: string) => void;
  className?: string;
}) {
  return (
    <div
      role="tablist"
      className={cn('scrollbar-none flex gap-1 overflow-x-auto border-b border-line', className)}
    >
      {items.map((it) => {
        const key = it.id ?? it.value ?? it.label;
        const active = key === value;
        return (
          <button
            key={key}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(key)}
            className={cn(
              'relative min-h-[44px] shrink-0 whitespace-nowrap px-4 text-sm font-medium transition-colors',
              active ? 'text-ink' : 'text-ink-3 hover:text-ink-2',
            )}
          >
            {it.label}
            {typeof it.badge === 'number' ? (
              <span className="ml-1.5 rounded-full bg-ink/[0.06] px-1.5 text-xs">{it.badge}</span>
            ) : null}
            {active ? (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-action" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({ children }: { children: ReactNode }) {
  return <div className="pt-4">{children}</div>;
}
