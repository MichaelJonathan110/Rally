import { Link } from 'react-router-dom';
import { Swords, CalendarDays, Coins } from 'lucide-react';
import { useTournaments } from '@/hooks/useTournaments';
import { Badge } from '@/components/ui/Badge';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { categoryMeta } from '@/config/categories';
import { formatCents } from '@/lib/utils';
import { dateTime } from '@/lib/format';

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draf',
  registration: 'Pendaftaran dibuka',
  open: 'Pendaftaran dibuka',
  in_progress: 'Berlangsung',
  completed: 'Selesai',
  cancelled: 'Dibatalkan',
};

const FORMAT_LABEL: Record<string, string> = {
  single_elimination: 'Gugur tunggal',
  double_elimination: 'Gugur ganda',
  round_robin: 'Setiap lawan',
};

export default function Tournaments() {
  const { data, isLoading, isError, refetch } = useTournaments({ limit: 24 });
  const items = data?.items ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-extrabold text-ink">Turnamen</h1>
        <p className="mt-1 text-sm text-ink-3">
          Kompetisi resmi komunitas RALLY - daftar, bertanding, dan naikkan peringkatmu.
        </p>
      </div>

      {isLoading ? (
        <SkeletonList count={6} />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : items.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((t) => {
            const meta = categoryMeta(t.category);
            return (
              <Link
                key={t.id}
                to={`/tournaments/${t.id}`}
                className="card flex flex-col gap-3 p-4 transition-all duration-300 ease-spring hover:-translate-y-0.5 hover:shadow-soft"
              >
                <div className="flex items-start justify-between gap-2">
                  <span
                    className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-paper-warm text-lg"
                    aria-hidden
                  >
                    {meta.emoji}
                  </span>
                  <Badge tone={t.status === 'completed' ? 'neutral' : 'success'}>
                    {STATUS_LABEL[t.status] ?? t.status}
                  </Badge>
                </div>
                <div className="min-w-0">
                  <h2 className="line-clamp-2 font-semibold text-ink">{t.name}</h2>
                  <p className="mt-0.5 text-sm text-ink-3">
                    {meta.label} · {FORMAT_LABEL[t.format] ?? t.format}
                  </p>
                </div>
                <ul className="mt-auto space-y-1 text-xs text-ink-3">
                  <li className="flex items-center gap-1.5">
                    <CalendarDays className="h-3.5 w-3.5" />
                    {t.starts_at ? dateTime(t.starts_at) : 'Jadwal menyusul'}
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Swords className="h-3.5 w-3.5" />
                    {t.max_entries} slot peserta
                  </li>
                  <li className="flex items-center gap-1.5 font-semibold text-ink">
                    <Coins className="h-3.5 w-3.5" />
                    {formatCents(t.entry_fee_cents, t.currency)}
                  </li>
                </ul>
              </Link>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={<Swords className="h-8 w-8" />}
          title="Belum ada turnamen"
          description="Turnamen komunitas akan muncul di sini setelah penyelenggara membukanya."
        />
      )}
    </div>
  );
}
