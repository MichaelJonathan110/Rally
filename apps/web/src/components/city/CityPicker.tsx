import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, MapPin } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useCities } from '@/hooks/useCatalog';
import { useCityStore, ALL_CITIES } from '@/store/city';
import { useT } from '@/i18n/strings';

/**
 * CitySelector - the persistent, changeable city picker that lives in the
 * header. It reads/writes `rally.city` through the city store, so home and
 * /discover both default to the chosen city. Always offers "all cities".
 */
export function CitySelector({
  className,
  compact = false,
}: {
  className?: string;
  /** Icon-only under the sm breakpoint when the header is tight. */
  compact?: boolean;
}) {
  const t = useT();
  const { data } = useCities();
  const city = useCityStore((s) => s.city);
  const hasChosen = useCityStore((s) => s.hasChosen);
  const setCity = useCityStore((s) => s.setCity);

  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const label = !hasChosen ? t('city.choose') : city ? city : t('common.allCities');

  const choose = (value: string) => {
    setCity(value);
    setOpen(false);
  };

  const cities = data ?? [];

  return (
    <div ref={ref} className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t('city.selectAria')}
        className={cn(
          'inline-flex h-10 max-w-[11rem] items-center gap-1.5 rounded-full border px-3 text-sm font-semibold transition-colors',
          hasChosen && city
            ? 'border-ink/15 bg-cyan-soft text-ink hover:border-ink/30'
            : 'border-line bg-surface text-ink-2 hover:border-ink/25 hover:text-ink',
        )}
      >
        <MapPin className="h-4 w-4 shrink-0" />
        <span className={cn('truncate', compact && 'hidden sm:inline')}>{label}</span>
        <ChevronDown className={cn('h-3.5 w-3.5 shrink-0 transition-transform', open && 'rotate-180')} />
      </button>

      {open ? (
        <div
          role="listbox"
          aria-label={t('city.listAria')}
          className="absolute right-0 z-50 mt-2 w-64 overflow-hidden rounded-2xl border border-line bg-surface p-1.5 shadow-lift animate-fade-in"
        >
          <p className="px-3 pb-1.5 pt-2 text-2xs font-semibold uppercase tracking-[0.14em] text-ink-3">
            {t('city.choose')}
          </p>
          <ul className="max-h-72 overflow-y-auto">
            <CityRow
              label={t('common.allCities')}
              active={hasChosen && city === ALL_CITIES}
              onClick={() => choose(ALL_CITIES)}
            />
            {cities.map((c) => (
              <CityRow
                key={c.city}
                label={c.city}
                count={c.count}
                active={hasChosen && city === c.city}
                onClick={() => choose(c.city)}
              />
            ))}
            {cities.length === 0 ? (
              <li className="px-3 py-3 text-sm text-ink-3">{t('city.loading')}</li>
            ) : null}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function CityRow({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count?: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <li>
      <button
        type="button"
        role="option"
        aria-selected={active}
        onClick={onClick}
        className={cn(
          'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition-colors',
          active ? 'bg-ink text-ink-inv' : 'text-ink hover:bg-ink/[0.05]',
        )}
      >
        <span className="flex-1 truncate font-medium">{label}</span>
        {typeof count === 'number' ? (
          <span className={cn('text-xs tabular-nums', active ? 'text-ink-inv/70' : 'text-ink-3')}>
            {count}
          </span>
        ) : null}
        {active ? <Check className="h-4 w-4 shrink-0" /> : null}
      </button>
    </li>
  );
}
