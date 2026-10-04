import { useMemo } from 'react';
import { Flame, CalendarClock, MapPin, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useActivities } from '@/hooks/useActivities';
import { ActivityCard } from '@/components/ActivityCard';
import { PageHeader } from '@/components/ui/PageHeader';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Badge } from '@/components/ui/Badge';
import { Reveal } from '@/components/motion/Reveal';
import { dayLabel, clock, isUpcoming, relative } from '@/lib/format';
import { categoryMeta } from '@/config/categories';

/**
 * Feed - the community pulse.
 *
 * Not a generic timeline: it leads with what is happening SOON (a live
 * "segera" rail) and then a chronological stream of real activities from the
 * API, each card carrying its category's pastel identity.
 */
export default function Feed() {
  const { data, isLoading, isError, refetch } = useActivities({ limit: 30 });

  const { soon, stream } = useMemo(() => {
    const items = [...(data?.items ?? [])];
    const upcoming = items
      .filter((a) => isUpcoming(a.starts_at) && !a.is_cancelled)
      .sort((a, b) => +new Date(a.starts_at) - +new Date(b.starts_at));
    return { soon: upcoming.slice(0, 3), stream: items };
  }, [data]);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Feed"
        title="Denyut komunitas"
        subtitle="Kegiatan terbaru dari seluruh Indonesia - yang segera mulai sampai yang baru dibuka."
      />

      {isLoading ? (
        <SkeletonList count={4} />
      ) : isError ? (
        <ErrorState title="Gagal memuat feed" onRetry={() => refetch()} />
      ) : stream.length === 0 ? (
        <EmptyState
          icon={<Flame className="h-8 w-8" />}
          title="Feed masih kosong"
          description="Belum ada kegiatan di feed. Buat kegiatan pertama dan ajak komunitasmu."
          action={
            <Link to="/create" className="font-medium text-action hover:underline">
              Buat kegiatan
            </Link>
          }
        />
      ) : (
        <>
          {soon.length > 0 ? (
            <section className="space-y-4">
              <SectionHeader
                eyebrow="Live"
                title="Segera mulai"
                action={
                  <Badge tone="danger">
                    <CalendarClock className="mr-1 h-3 w-3" /> Hari ini dan besok
                  </Badge>
                }
              />
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {soon.map((a) => {
                  const meta = categoryMeta(a.category);
                  return (
                    <Link
                      key={a.id}
                      to={`/activities/${a.id}`}
                      className="group flex flex-col gap-2 rounded-2xl border border-line bg-surface p-4 transition-all duration-300 hover:-translate-y-1 hover:shadow-lift"
                    >
                      <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-ink-3">
                        <span aria-hidden>{meta.emoji}</span>
                        {meta.label}
                      </span>
                      <p className="line-clamp-2 font-display text-base font-bold leading-snug text-ink">
                        {a.title}
                      </p>
                      <p className="mt-auto flex items-center gap-1.5 text-sm text-ink-2">
                        <CalendarClock className="h-4 w-4 text-ink-3" />
                        {dayLabel(a.starts_at)} - {clock(a.starts_at)}
                      </p>
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-action">
                        {relative(a.starts_at)}
                        <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                      </span>
                    </Link>
                  );
                })}
              </div>
            </section>
          ) : null}

          <section className="space-y-4">
            <SectionHeader
              eyebrow="Terbaru"
              title="Semua kegiatan"
              action={
                <Link
                  to="/discover"
                  className="inline-flex items-center gap-1 text-sm font-semibold text-action hover:underline"
                >
                  <MapPin className="h-4 w-4" /> Jelajah
                </Link>
              }
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {stream.map((a, i) => (
                <Reveal key={a.id} delay={(i % 3) * 50}>
                  <ActivityCard activity={a} className="h-full" />
                </Reveal>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
