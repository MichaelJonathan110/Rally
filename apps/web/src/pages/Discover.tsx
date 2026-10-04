import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, SlidersHorizontal, Compass } from 'lucide-react';
import { useActivities } from '@/hooks/useActivities';
import { ActivityCard } from '@/components/ActivityCard';
import { PageHeader } from '@/components/ui/PageHeader';
import { Chip } from '@/components/ui/Chip';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Reveal } from '@/components/motion/Reveal';
import { CATEGORIES } from '@/config/categories';
import { useActivityTypes } from '@/hooks/useCatalog';
import { useCityStore } from '@/store/city';
import { useT } from '@/i18n/strings';

const SKILL_VALUES = ['', 'beginner', 'intermediate', 'advanced', 'expert'];
const SKILL_LABELS: Record<string, string> = {
  '': 'Semua level',
  beginner: 'Pemula',
  intermediate: 'Menengah',
  advanced: 'Mahir',
  expert: 'Expert',
};

export default function Discover() {
  const t = useT();
  const [params, setParams] = useSearchParams();
  const [term, setTerm] = useState('');
  const [page, setPage] = useState(1);
  const limit = 12;

  // Default to the chosen city (from onboarding / the header picker). The URL
  // `city` param wins so shared links keep working.
  const chosenCity = useCityStore((s) => s.city);
  const city = params.get('city') ?? chosenCity ?? '';

  const category = params.get('sport_category') ?? '';
  const type = params.get('type') ?? '';
  const skill = params.get('skill_level') ?? '';
  const sort = params.get('sort') ?? 'soonest';

  const { data: types } = useActivityTypes();

  // Category narrows the type chips; a type chip sends ?type=<slug>.
  const typeOptions = useMemo(() => {
    const all = types ?? [];
    return category ? all.filter((x) => x.category === category) : all;
  }, [types, category]);

  const filters = useMemo(
    () => ({
      limit,
      offset: (page - 1) * limit,
      search: term || undefined,
      sport_category: category || undefined,
      type: type || undefined,
      skill_level: skill || undefined,
      city: city || undefined,
    }),
    [page, limit, term, category, type, skill, city],
  );

  const { data, isLoading, isError, refetch, isFetching } = useActivities(filters);

  const items = useMemo(() => {
    if (!data) return [];
    const copy = [...data.items];
    if (sort === 'cheapest') copy.sort((a, b) => a.cost_per_person_cents - b.cost_per_person_cents);
    else if (sort === 'popular') copy.sort((a, b) => b.participant_count - a.participant_count);
    else {
      // "Soonest" must mean *upcoming* soonest: already-started events sink to
      // the bottom so yesterday's kegiatan never leads the list.
      const now = Date.now();
      copy.sort((a, b) => {
        const aPast = +new Date(a.starts_at) < now ? 1 : 0;
        const bPast = +new Date(b.starts_at) < now ? 1 : 0;
        if (aPast !== bPast) return aPast - bPast;
        return +new Date(a.starts_at) - +new Date(b.starts_at);
      });
    }
    return copy;
  }, [data, sort]);

  const update = (key: string, value: string, clear: string[] = []) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    for (const k of clear) next.delete(k);
    setParams(next, { replace: true });
    setPage(1);
  };

  const skillOptions = SKILL_VALUES.map((v) => ({ value: v, label: SKILL_LABELS[v] }));
  const sortOptions = [
    { value: 'soonest', label: t('discover.sortSoonest') },
    { value: 'cheapest', label: t('discover.sortCheapest') },
    { value: 'popular', label: t('discover.sortPopular') },
  ];

  const hasFilters = Boolean(term || category || type || skill || city);
  const totalPages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t('discover.eyebrow')}
        title={t('discover.title')}
        subtitle={
          city ? t('discover.scopedTo', { city }) : t('discover.subtitle')
        }
      />

      <div className="relative">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3" />
        <Input
          aria-label={t('discover.searchLabel')}
          placeholder={t('discover.searchPlaceholder')}
          className="h-12 pl-10"
          value={term}
          onChange={(e) => {
            setTerm(e.target.value);
            setPage(1);
          }}
        />
      </div>

      <div className="-mx-4 flex snap-x snap-mandatory gap-2 overflow-x-auto px-4 pb-2 no-scrollbar [&>*]:shrink-0 [&>*]:snap-start sm:mx-0 sm:px-0">
        <Chip active={!category} onClick={() => update('sport_category', '', ['type'])}>
          <Compass className="h-4 w-4" /> {t('common.all')}
        </Chip>
        {CATEGORIES.map((c) => (
          <Chip
            key={c.id}
            active={category === c.id}
            onClick={() => update('sport_category', c.id, ['type'])}
          >
            <span aria-hidden>{c.emoji}</span> {c.label}
          </Chip>
        ))}
      </div>

      {typeOptions.length > 0 ? (
        <div className="space-y-2">
          <p className="text-2xs font-semibold uppercase tracking-[0.14em] text-ink-3">
            {t('type.title')}
          </p>
          <div
            className="-mx-4 flex snap-x snap-mandatory gap-2 overflow-x-auto px-4 pb-2 no-scrollbar [&>*]:shrink-0 [&>*]:snap-start sm:mx-0 sm:px-0"
            role="group"
            aria-label={t('type.filterHint')}
          >
            <Chip active={!type} onClick={() => update('type', '')}>
              {t('type.all')}
            </Chip>
            {typeOptions.map((x) => (
              <Chip
                key={x.slug}
                active={type === x.slug}
                onClick={() => update('type', x.slug)}
              >
                {x.label_id}
              </Chip>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Select
          label={t('discover.level')}
          options={skillOptions}
          value={skill}
          onChange={(e) => update('skill_level', e.target.value)}
        />
        <Select
          label={t('discover.sort')}
          options={sortOptions}
          value={sort}
          onChange={(e) => update('sort', e.target.value)}
        />
      </div>

      {hasFilters ? (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setTerm('');
            setParams(new URLSearchParams(), { replace: true });
            setPage(1);
          }}
        >
          <SlidersHorizontal className="h-4 w-4" /> {t('common.reset')}
        </Button>
      ) : null}

      {isLoading ? (
        <SkeletonList count={6} />
      ) : isError ? (
        <ErrorState title={t('discover.errorTitle')} onRetry={() => refetch()} />
      ) : data && data.items.length > 0 ? (
        <>
          <p className="text-sm text-ink-3">
            <span className="font-semibold text-ink">{data.total}</span>{' '}
            {t('discover.foundLabel')}
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {items.map((a, i) => (
              <Reveal key={a.id} delay={(i % 4) * 50}>
                <ActivityCard activity={a} className="h-full" />
              </Reveal>
            ))}
          </div>
          {totalPages > 1 ? (
            <div className="flex items-center justify-center gap-3 pt-2">
              <Button
                variant="outline"
                disabled={page <= 1 || isFetching}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                {t('discover.prev')}
              </Button>
              <span className="text-sm text-ink-3">
                {t('discover.page', { page, total: totalPages })}
              </span>
              <Button
                variant="outline"
                disabled={page >= totalPages || isFetching}
                onClick={() => setPage((p) => p + 1)}
              >
                {t('discover.next')}
              </Button>
            </div>
          ) : null}
        </>
      ) : (
        <EmptyState
          icon={<Compass className="h-8 w-8" />}
          title={t('discover.emptyTitle')}
          description={t('discover.emptyDesc')}
        />
      )}
    </div>
  );
}
