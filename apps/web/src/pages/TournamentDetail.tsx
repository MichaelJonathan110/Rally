import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Trophy, CalendarDays, Swords, Coins } from 'lucide-react';
import { useTournament, useTournamentStandings } from '@/hooks/useTournaments';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { categoryMeta } from '@/config/categories';
import { formatCents } from '@/lib/utils';
import { dateTime, formatLabel } from '@/lib/format';

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draf',
  registration: 'Pendaftaran dibuka',
  open: 'Pendaftaran dibuka',
  in_progress: 'Berlangsung',
  completed: 'Selesai',
  cancelled: 'Dibatalkan',
};

export default function TournamentDetail() {
  const { id = '' } = useParams();
  const tournament = useTournament(id);
  const standings = useTournamentStandings(id);

  if (tournament.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (tournament.isError || !tournament.data) {
    return <ErrorState title="Turnamen tidak ditemukan" onRetry={() => tournament.refetch()} />;
  }

  const t = tournament.data;
  const meta = categoryMeta(t.category);
  const rows = standings.data?.standings ?? [];

  return (
    <div className="space-y-5">
      <Link
        to="/tournaments"
        className="inline-flex items-center gap-1.5 text-sm text-ink-3 hover:text-action"
      >
        <ArrowLeft className="h-4 w-4" /> Semua turnamen
      </Link>

      <div className="card space-y-3 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="font-display text-2xl font-extrabold text-ink">{t.name}</h1>
          <Badge tone={t.status === 'completed' ? 'neutral' : 'success'}>
            {STATUS_LABEL[t.status] ?? t.status}
          </Badge>
        </div>
        <p className="text-sm text-ink-2">
          {meta.emoji} {meta.label} · {formatLabel(t.format)}
        </p>
        <div className="grid grid-cols-1 gap-2 text-sm text-ink-2 sm:grid-cols-3">
          <p className="flex items-center gap-2">
            <CalendarDays className="h-4 w-4" />
            {t.starts_at ? dateTime(t.starts_at) : 'Jadwal menyusul'}
          </p>
          <p className="flex items-center gap-2">
            <Swords className="h-4 w-4" />
            {t.max_entries} slot
          </p>
          <p className="flex items-center gap-2 font-semibold text-ink">
            <Coins className="h-4 w-4" />
            {formatCents(t.entry_fee_cents, t.currency)}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader title="Klasemen" subtitle="Urutan peserta turnamen" />
        {standings.isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : rows.length > 0 ? (
          <ol className="divide-y divide-line">
            {rows.map((row, i) => (
              <li key={row.entry_id} className="flex items-center gap-3 py-3">
                <span
                  className={
                    row.rank <= 3
                      ? 'w-9 text-center font-bold text-warning'
                      : 'w-9 text-center font-bold text-ink-3'
                  }
                >
                  #{row.rank}
                </span>
                <span className="min-w-0 flex-1 line-clamp-1 text-sm text-ink">
                  Peserta #{i + 1}
                </span>
              </li>
            ))}
          </ol>
        ) : (
          <EmptyState
            icon={<Trophy className="h-8 w-8" />}
            title="Belum ada klasemen"
            description="Klasemen muncul setelah peserta terdaftar dan pertandingan dimulai."
          />
        )}
      </Card>
    </div>
  );
}
