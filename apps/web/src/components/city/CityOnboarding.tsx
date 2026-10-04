import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useCityStore } from '@/store/city';
import { useT } from '@/i18n/strings';

/**
 * CityOnboarding - the compact first-visit step on the home hero.
 *
 * RALLY should ask "where are you?" before it shows "nearby" activities. The
 * original inline city heading + subtitle + chip grid has been removed from
 * the hero; choosing a city now lives in the header picker (`CityPicker`).
 * This component only renders the compact confirmation chip once a city is
 * known.
 */
export function CityOnboarding({ className }: { className?: string }) {
  const t = useT();
  const hasChosen = useCityStore((s) => s.hasChosen);
  const city = useCityStore((s) => s.city);
  const clearCity = useCityStore((s) => s.clearCity);

  if (!hasChosen) return null;

  // Compact confirmation once a city is known.
  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3.5 py-2 text-sm shadow-soft',
        className,
      )}
    >
      <span className="grid h-6 w-6 place-items-center rounded-full bg-mint text-ink">
        <Check className="h-3.5 w-3.5" />
      </span>
      <span className="text-ink-2">
        {city ? (
          <>
            {t('city.showing')} <span className="font-semibold text-ink">{city}</span>
          </>
        ) : (
          <span className="font-semibold text-ink">{t('city.showingAll')}</span>
        )}
      </span>
      <button
        type="button"
        onClick={() => {
          clearCity();
        }}
        className="font-semibold text-action hover:underline"
      >
        {t('city.change')}
      </button>
    </div>
  );
}
