import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Trophy } from 'lucide-react';
import { useActivities } from '@/hooks/useActivities';
import { useLeaderboard } from '@/hooks/useLeaderboard';
import { useAuth } from '@/hooks/useAuth';
import { Select } from '@/components/ui/Select';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { MmrEmblem } from '@/components/visuals/MmrEmblem';

const PERIODS = [
  { value: 'all_time', label: 'Sepanjang waktu' },
  { value: 'monthly', label: 'Bulan ini' },
  { value: 'weekly', label: 'Minggu ini' },
];

export default function Leaderboard() {
  const { user } = useAuth();
  const activities = useActivities({ limit: 50 });
  const [activityId, setActivityId] = useState('');
  const [period, setPeriod] = useState('all_time');

  const effectiveId = activityId || activities.data?.items[0]?.id || '';
  const board = useLeaderboard(effectiveId || undefined, period);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">Papan Peringkat</h1>
          <p className="mt-1 text-sm text-ink-3">Peringkat MMR per kategori kegiatan.</p>
        </div>
        <Badge tone="accent">
          <Trophy className="mr-1 h-3 w-3" /> {period.replace('_', ' ')}
        </Badge>
      </div>

      <div className="card grid grid-cols-1 gap-3 p-4 sm:grid-cols-2">
        <Select
          label="Kegiatan"
          options={
            activities.data?.items.map((a) => ({ value: a.id, label: a.title })) ?? [
              { value: '', label: 'Memuat kegiatan...' },
            ]
          }
          value={effectiveId}
          onChange={(e) => setActivityId(e.target.value)}
        />
        <Select
          label="Periode"
          options={PERIODS}
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
        />
      </div>

      <Card>
        <CardHeader title="Peringkat" subtitle="MMR langsung dari API RALLY" />
        {!user ? (
          <EmptyState
            icon={<MmrEmblem className="w-24" />}
            title="Masuk untuk melihat peringkat"
            description="Papan peringkat perlu masuk akun."
            action={
              <Link to="/login" className="font-medium text-action hover:underline">
                Masuk
              </Link>
            }
          />
        ) : board.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : board.isError ? (
          <EmptyState
            icon={<MmrEmblem className="w-20" />}
            title="Belum ada data peringkat"
            description="Main pertandingan di kategori ini untuk membuat peringkat."
          />
        ) : board.data && board.data.length > 0 ? (
          <ol className="divide-y divide-line">
            {board.data.map((e) => (
              <li key={e.id} className="flex items-center gap-3 py-3">
                <span
                  className={
                    e.rank <= 3
                      ? 'w-9 text-center text-base font-bold text-warning'
                      : 'w-9 text-center text-base font-bold text-ink-3'
                  }
                >
                  #{e.rank}
                </span>
                <span className="min-w-0 flex-1 line-clamp-1 text-sm text-ink">
                  {e.user_id === user.id ? 'Kamu' : `Pemain ${e.user_id.slice(0, 8)}`}
                </span>
                <span className="text-sm text-ink-3">{e.games_played} pertandingan</span>
                <span className="font-semibold text-action">{Math.round(e.rating)}</span>
              </li>
            ))}
          </ol>
        ) : (
          <EmptyState
            icon={<MmrEmblem className="w-20" />}
            title="Belum ada peringkat"
            description="Kategori ini belum punya pemain berperingkat."
          />
        )}
      </Card>
    </div>
  );
}
