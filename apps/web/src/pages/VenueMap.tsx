import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, Layers, MapPin, Navigation, Search } from 'lucide-react';
import { useVenueMap } from '@/hooks/useDiscovery';
import { PageHeader } from '@/components/ui/PageHeader';
import { Select } from '@/components/ui/Select';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { categoryMeta, CATEGORIES, TONE } from '@/config/categories';
import { cn } from '@/lib/utils';
import type { MapVenue } from '@/api/types';

const ALL = '';
const sportLabel = (slug: string) =>
  slug
    .split(/[-_]/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');

function project(
  v: MapVenue,
  bounds: { min_lat: number; max_lat: number; min_lng: number; max_lng: number },
) {
  const spanLng = bounds.max_lng - bounds.min_lng || 1;
  const spanLat = bounds.max_lat - bounds.min_lat || 1;
  const clamp = (n: number) => Math.max(3, Math.min(97, n));
  return {
    x: clamp(((v.longitude - bounds.min_lng) / spanLng) * 100),
    y: clamp(((bounds.max_lat - v.latitude) / spanLat) * 100),
  };
}

export default function VenueMap() {
  const [category, setCategory] = useState(ALL);
  const [city, setCity] = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [legendOpen, setLegendOpen] = useState(true);

  const { data, isLoading, isError } = useVenueMap({
    category: category || undefined,
    city: city || undefined,
  });

  const venues = data?.venues ?? [];
  const bounds = data?.bounds;

  const categoriesPresent = useMemo(() => {
    const ids = new Set(venues.map((v) => v.category ?? 'other'));
    return CATEGORIES.filter((c) => ids.has(c.id));
  }, [venues]);

  const selectedVenue = venues.find((v) => v.id === selected) ?? null;
  const selectedRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (selected && selectedRef.current) {
      selectedRef.current.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }
  }, [selected]);

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Jelajah"
        title="Peta Venue"
        subtitle="Temukan lapangan dan arena di seluruh Indonesia lewat peta interaktif."
      />

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <Select
          label="Kategori"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setSelected(null);
          }}
          options={[
            { value: ALL, label: 'Semua kategori' },
            ...CATEGORIES.map((c) => ({ value: c.id, label: c.emoji + ' ' + c.label })),
          ]}
        />
        <Input
          label="Cari kota"
          placeholder="Misal: Jakarta"
          value={city}
          onChange={(e) => {
            setCity(e.target.value);
            setSelected(null);
          }}
          leftIcon={<Search className="h-4 w-4" />}
        />
        <p className="rounded-xl border border-line bg-surface-muted px-3 py-2 text-center text-sm text-ink-3 sm:text-left">
          Menampilkan <span className="font-semibold text-ink">{venues.length}</span> dari{' '}
          <span className="font-semibold text-ink">{data?.count ?? venues.length}</span> venue
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-[460px] w-full rounded-2xl" />
      ) : isError || !bounds || venues.length === 0 ? (
        <EmptyState
          icon={<MapPin className="h-8 w-8" />}
          title="Belum ada venue di peta"
          description="Coba ubah kategori atau kata kunci kota pencarian."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <div className="relative overflow-hidden rounded-2xl border border-line bg-gradient-to-br from-cyan-soft via-surface to-lime-soft shadow-soft">
            <div
              className="pointer-events-none absolute inset-0"
              style={{
                backgroundImage:
                  'linear-gradient(rgba(20,20,20,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(20,20,20,0.06) 1px, transparent 1px)',
                backgroundSize: '8% 8%',
              }}
              aria-hidden
            />
            <div
              className="pointer-events-none absolute inset-0"
              style={{
                backgroundImage:
                  'radial-gradient(70% 60% at 20% 15%, rgba(159,227,220,0.55) 0%, transparent 60%), radial-gradient(60% 55% at 85% 80%, rgba(217,240,140,0.45) 0%, transparent 60%)',
              }}
              aria-hidden
            />

            <div className="relative h-[460px] w-full">
              {venues.map((v) => {
                const { x, y } = project(v, bounds);
                const tone = TONE[categoryMeta(v.category ?? 'other').tone];
                const active = v.id === selected;
                return (
                  <button
                    key={v.id}
                    ref={active ? selectedRef : undefined}
                    type="button"
                    aria-label={'Venue ' + v.name + ' di ' + v.city}
                    title={v.name + ' - ' + v.city}
                    onClick={() => setSelected(v.id)}
                    className={cn(
                      'group absolute -translate-x-1/2 -translate-y-1/2 rounded-full outline-none',
                      'transition-transform duration-200 ease-spring hover:z-20 hover:scale-150 focus-visible:z-20 focus-visible:scale-150',
                      active && 'z-20 scale-150',
                    )}
                    style={{ left: x + '%', top: y + '%' }}
                  >
                    {active ? (
                      <span
                        className="absolute inset-0 -z-10 animate-pulse-ring rounded-full"
                        style={{ backgroundColor: tone.hex }}
                        aria-hidden
                      />
                    ) : null}
                    <span
                      className={cn(
                        'block h-3.5 w-3.5 rounded-full border shadow-sm ring-2 transition-colors',
                        active
                          ? 'border-ink ring-ink/30'
                          : 'border-ink/25 ring-transparent group-hover:ring-ink/20',
                      )}
                      style={{ backgroundColor: tone.hex }}
                      aria-hidden
                    />
                  </button>
                );
              })}
            </div>

            {selectedVenue ? (
              <div className="absolute bottom-3 left-3 right-3 rounded-xl border border-line bg-surface/95 p-3 shadow-lift backdrop-blur-sm sm:right-auto sm:w-80">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-display text-base font-bold text-ink">{selectedVenue.name}</h3>
                  <Badge tone="success">{selectedVenue.court_count} lapangan</Badge>
                </div>
                <p className="mt-1 flex items-center gap-1.5 text-sm text-ink-3">
                  <MapPin className="h-4 w-4 shrink-0" />
                  {selectedVenue.city}
                  {selectedVenue.area ? ' - ' + selectedVenue.area : ''}
                </p>
                {selectedVenue.sport_slugs.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {selectedVenue.sport_slugs.slice(0, 5).map((s) => (
                      <Badge key={s} tone="neutral">
                        {sportLabel(s)}
                      </Badge>
                    ))}
                  </div>
                ) : null}
                <Link
                  to={'/venues/' + selectedVenue.id}
                  className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-action hover:underline"
                >
                  Lihat detail
                  <Navigation className="h-3.5 w-3.5" />
                </Link>
              </div>
            ) : null}
          </div>

          <div className="space-y-4">
            {categoriesPresent.length > 0 ? (
              <div className="card overflow-hidden">
                <button
                  type="button"
                  onClick={() => setLegendOpen((o) => !o)}
                  aria-expanded={legendOpen}
                  className="flex w-full items-center justify-between gap-2 p-4 text-left"
                >
                  <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                    <Layers className="h-4 w-4 text-ink-3" />
                    Legenda kategori
                  </span>
                  <ChevronDown
                    className={cn(
                      'h-4 w-4 text-ink-3 transition-transform',
                      legendOpen && 'rotate-180',
                    )}
                  />
                </button>
                {legendOpen ? (
                  <ul className="grid grid-cols-2 gap-2 border-t border-line p-4">
                    {categoriesPresent.map((c) => (
                      <li key={c.id} className="flex items-center gap-2 text-sm text-ink-2">
                        <span
                          className="h-3 w-3 shrink-0 rounded-full ring-2 ring-ink/10"
                          style={{ backgroundColor: TONE[c.tone].hex }}
                          aria-hidden
                        />
                        {c.emoji} {c.label}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}

            <div className="card overflow-hidden">
              <div className="flex items-center justify-between gap-2 border-b border-line p-4">
                <h3 className="text-sm font-semibold text-ink">Daftar venue</h3>
                <span className="text-xs text-ink-3">{venues.length} titik</span>
              </div>
              <ul className="max-h-[26rem] divide-y divide-line overflow-y-auto">
                {venues.map((v) => {
                  const active = v.id === selected;
                  const tone = TONE[categoryMeta(v.category ?? 'other').tone];
                  return (
                    <li key={v.id}>
                      <button
                        type="button"
                        onClick={() => setSelected(v.id)}
                        className={cn(
                          'flex w-full items-center gap-3 p-3 text-left transition-colors',
                          active ? 'bg-action/[0.06]' : 'hover:bg-ink/[0.02]',
                        )}
                      >
                        <span
                          className={cn(
                            'h-2.5 w-2.5 shrink-0 rounded-full ring-2',
                            active ? 'ring-ink/30' : 'ring-transparent',
                          )}
                          style={{ backgroundColor: tone.hex }}
                          aria-hidden
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-semibold text-ink">
                            {v.name}
                          </span>
                          <span className="block truncate text-xs text-ink-3">
                            {v.city} - {v.court_count} lapangan
                          </span>
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
