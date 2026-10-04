import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { CATEGORIES, TONE } from '@/config/categories';

/**
 * Category navigation that is ALSO a visual index: each tile carries the
 * category's pastel tone and photograph, so it never reads as a row of
 * identical chips. Links to Discover pre-filtered, so the tile is a real
 * control - not decoration.
 */
export function CategoryRail({ activeCategory }: { activeCategory?: string }) {
  return (
    <div className="-mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-2 no-scrollbar sm:mx-0 sm:px-0">
      {CATEGORIES.map((c) => {
        const tone = TONE[c.tone];
        const active = activeCategory === c.id;
        return (
          <Link
            key={c.id}
            to={`/discover?sport_category=${c.id}`}
            aria-current={active ? 'page' : undefined}
            className={cn(
              'group relative flex w-[8.5rem] shrink-0 snap-start flex-col justify-between gap-6 overflow-hidden rounded-xl border p-3 transition-all duration-300 ease-spring hover:-translate-y-1 hover:shadow-lift',
              active ? 'border-ink' : 'border-line',
              'bg-surface',
            )}
          >
            <span
              className={cn(
                'grid h-11 w-11 place-items-center rounded-xl text-xl transition-transform duration-500 ease-spring group-hover:scale-110',
                tone.solid,
              )}
              aria-hidden
            >
              {c.emoji}
            </span>
            <span>
              <span className="block text-sm font-bold leading-tight text-ink">{c.label}</span>
              <span className="mt-0.5 block text-2xs text-ink-3">{c.blurb}</span>
            </span>
            <span
              className={cn(
                'absolute -right-6 -top-6 h-16 w-16 rounded-full opacity-60 transition-transform duration-500 ease-spring group-hover:scale-125',
                tone.soft,
              )}
              aria-hidden
            />
          </Link>
        );
      })}
    </div>
  );
}
