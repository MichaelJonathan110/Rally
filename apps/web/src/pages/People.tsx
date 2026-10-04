import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Trophy, Swords } from 'lucide-react';
import { useActivities } from '@/hooks/useActivities';
import { useLeaderboard } from '@/hooks/useLeaderboard';
import { useAuth } from '@/hooks/useAuth';
import { Select } from '@/components/ui/Select';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { PageHeader } from '@/components/ui/PageHeader';
import { categoryMeta } from '@/config/categories';

const PERIODS = [
  { value: 'all_time', label: 'Sepanjang waktu' },
  { value: 'monthly', label: 'Bulan ini' },
  { value: 'weekly', label: 'Minggu ini' },
];

/** MMR band -> label + tone, so a number reads as a rank a human understands. */
function mmrBand(rating: number) {
  if (rating >= 1600) return { label: 'Elite', tone: 'accent' as const };
  if (rating >= 1400) return { label: 'Mahir', tone: 'success' as const };
  if (rating >= 1200) return { label: 'Menengah', tone: 'warning' as const };
  return { label: 'Pemula', tone: 'neutral' as const };
}

export default function People() {
  const { user } = useAuth();
  const activities = useActivities({ limit: 50 });
  const [activityId, setActivityId] = useState('');
  const [period, setPeriod] = useState('all_time');

  const effectiveId = activityId || activities.data?.items[0]?.id || '';
  const selected = activities.data?.items.find((a) => a.id === effectiveId);
  // Only hit the protected leaderboard endpoint when signed in; guests get an
  // honest empty state instead of a 401.
  const board = useLeaderboard(user ? effectiveId || undefined : undefined, period);

  const rows = board.data ?? [];

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Komunitas"
        title="Orang & MMR"
        subtitle="Kenali pemain di sekitarmu dan lihat peringkat MMR mereka per kategori kegiatan."
      />

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
        <CardHeader
          title={selected ? `Pemain · ${selected.title}` : 'Pemain'}
          subtitle="MMR langsung dari API RALLY"
          action={
            selected ? (
              <Badge tone="accent">
                <Swords className="mr-1 h-3 w-3" />
                {categoryMeta(selected.category).label}
              </Badge>
            ) : null
          }
        />

        {!user ? (
          <EmptyState
            icon={<Users className="h-8 w-8" />}
            title="Masuk untuk melihat daftar orang & MMR"
            description="Data pemain dan MMR hanya tersedia untuk akun yang sudah masuk."
            action={
              <Link to="/login" className="font-medium text-action hover:underline">
                Masuk
              </Link>
            }
          />
        ) : board.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : board.isError ? (
          <EmptyState
            icon={<Users className="h-8 w-8" />}
            title="Gagal memuat pemain"
            description="Coba pilih kegiatan lain atau muat ulang halaman."
          />
        ) : rows.length > 0 ? (
          <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {rows.map((e) => {
              const band = mmrBand(e.rating);
              const isMe = e.user_id === user.id;
              const name = isMe ? 'Kamu' : `Pemain ${e.user_id.slice(0, 8)}`;
              return (
                <li
                  key={e.id}
                  className="flex items-center gap-3 rounded-xl border border-line bg-surface p-3"
                >
                  <span
                    className={
                      e.rank <= 3
                        ? 'w-6 text-center text-sm font-bold text-warning'
                        : 'w-6 text-center text-sm font-bold text-ink-3'
                    }
                  >
                    {e.rank}
                  </span>
                  <Avatar name={name} size={38} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink">{name}</p>
                    <p className="text-xs text-ink-3">{e.games_played} pertandingan</p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="font-semibold text-action">{Math.round(e.rating)}</span>
                    <Badge tone={band.tone}>{band.label}</Badge>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState
            icon={<Trophy className="h-8 w-8" />}
            title="Belum ada pemain berperingkat"
            description="Kategori ini belum punya pemain dengan MMR. Main pertandingan untuk mengisi daftar."
          />
        )}
      </Card>
    </div>
  );
}
