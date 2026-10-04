import { Link } from 'react-router-dom';
import { CalendarPlus } from 'lucide-react';
import { useMyActivities } from '@/hooks/useActivities';
import { ActivityCard } from '@/components/ActivityCard';
import { Skeleton } from '@/components/ui/Skeleton';

/**
 * "Aktivitas Saya" - what the signed-in user has actually joined or is
 * hosting, soonest first. Renders nothing for guests so the rail only ever
 * appears when it has real, personal value.
 */
export function MyActivitiesRail() {
  const { data, isLoading } = useMyActivities({ active_only: true, limit: 6 });
  const items = data?.items ?? [];

  if (isLoading) {
    return (
      <div className="flex gap-3 overflow-hidden">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-[88px] w-64 shrink-0 rounded-xl" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-line bg-surface/60 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-lime-soft text-ink">
            <CalendarPlus className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-ink">Belum ada kegiatan mendatang</p>
            <p className="text-xs text-ink-3">
              Ikut kegiatan atau buat milikmu sendiri - akan muncul di sini.
            </p>
          </div>
        </div>
        <Link
          to="/discover"
          className="inline-flex h-10 items-center rounded-full bg-ink px-4 text-sm font-semibold text-ink-inv transition-colors hover:bg-ink/90"
        >
          Jelajahi kegiatan
        </Link>
      </div>
    );
  }

  return (
    <div className="-mx-4 flex snap-x gap-3 overflow-x-auto px-4 pb-1 no-scrollbar sm:mx-0 sm:px-0">
      {items.map((a) => (
        <ActivityCard key={a.id} activity={a} variant="compact" className="w-72 shrink-0 snap-start" />
      ))}
    </div>
  );
}
