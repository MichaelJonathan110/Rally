import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import { Calendar, MapPin, Users, Trophy, Info, UserPlus, LogOut } from 'lucide-react';
import {
  useActivity,
  useActivityParticipants,
  useJoinActivity,
  useLeaveActivity,
} from '@/hooks/useActivities';
import { useLeaderboard } from '@/hooks/useLeaderboard';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader } from '@/components/ui/Card';
import { Tabs } from '@/components/ui/Tabs';
import { Avatar } from '@/components/ui/Avatar';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCents } from '@/lib/utils';
import {
  cleanDescription,
  categoryLabel,
  levelLabel,
  formatDateID,
  participantStatusLabel,
} from '@/lib/format';

export default function ActivityDetail() {
  const { id = '' } = useParams();
  const { user } = useAuth();
  const [tab, setTab] = useState('about');

  const activity = useActivity(id);
  const participants = useActivityParticipants(id);
  const leaderboard = useLeaderboard(id);
  const join = useJoinActivity(id);
  const leave = useLeaveActivity(id);

  if (activity.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (activity.isError || !activity.data) {
    return <ErrorState title="Kegiatan tidak ditemukan" onRetry={() => activity.refetch()} />;
  }

  const a = activity.data;
  const mine = participants.data?.find((p) => p.user_id === user?.id);
  const price = formatCents(a.cost_per_person_cents, a.currency);
  const full = a.participant_count >= a.max_participants;

  return (
    <div className="space-y-5">
      <Link to="/discover" className="text-sm text-ink-3 hover:text-action">
        &larr; Kembali ke Jelajah
      </Link>

      <div className="card space-y-4 p-5 sm:p-6">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="accent">{categoryLabel(a.category)}</Badge>
          <Badge tone="neutral">{levelLabel(a.skill_level)}</Badge>
          {a.is_cancelled ? <Badge tone="danger">Dibatalkan</Badge> : null}
        </div>
        <h1 className="text-2xl font-bold text-ink sm:text-3xl">{a.title}</h1>
        <div className="grid grid-cols-1 gap-2 text-sm text-ink-2 sm:grid-cols-2">
          <p className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            {formatDateID(a.starts_at)}
          </p>
          <p className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            {a.participant_count}/{a.max_participants} peserta
          </p>
          <p className="flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            {a.venue_id ? (
              <Link to={`/venues/${a.venue_id}`} className="hover:text-action">
                Lihat venue
              </Link>
            ) : (
              'Venue belum ditentukan'
            )}
          </p>
          <p className="flex items-center gap-2 font-semibold text-action">{price} / orang</p>
        </div>

        <div className="flex flex-wrap gap-3 pt-1">
          {!user ? (
            <Link to="/login">
              <Button>Masuk untuk ikut</Button>
            </Link>
          ) : mine && mine.status !== 'cancelled' && mine.status !== 'declined' ? (
            <Button variant="outline" loading={leave.isPending} onClick={() => leave.mutate()}>
              <LogOut className="h-4 w-4" /> Keluar dari kegiatan
            </Button>
          ) : (
            <Button
              loading={join.isPending}
              disabled={full || a.is_cancelled}
              onClick={() => join.mutate()}
            >
              <UserPlus className="h-4 w-4" /> {full ? 'Kegiatan penuh' : 'Ikut kegiatan'}
            </Button>
          )}
        </div>
      </div>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          { value: 'about', label: 'Tentang' },
          { value: 'participants', label: 'Peserta' },
          { value: 'matches', label: 'Pertandingan' },
          { value: 'leaderboard', label: 'Papan Peringkat' },
        ]}
      />

      {tab === 'about' && (
        <Card>
          <CardHeader title="Tentang kegiatan ini" />
          <p className="whitespace-pre-line text-sm text-ink-2">
            {cleanDescription(a.description, a.title) || 'Host belum menuliskan deskripsi.'}
          </p>
        </Card>
      )}

      {tab === 'participants' && (
        <Card>
          <CardHeader title="Peserta" subtitle={`${a.participant_count} bergabung`} />
          {participants.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : participants.data && participants.data.length > 0 ? (
            <ul className="divide-y divide-line">
              {participants.data.map((p, i) => (
                <li key={p.id} className="flex items-center gap-3 py-3">
                  <Avatar name={`#${i + 1}`} size={36} />
                  <div className="min-w-0">
                    <p className="line-clamp-1 text-sm text-ink">
                      {p.user_id === user?.id ? 'Kamu' : `Peserta #${i + 1}`}
                    </p>
                    <p className="text-xs text-ink-3">{participantStatusLabel(p.status)}</p>
                  </div>
                  {p.is_host ? (
                    <Badge tone="accent" className="ml-auto">
                      Host
                    </Badge>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="Belum ada peserta" description="Jadilah yang pertama bergabung." />
          )}
        </Card>
      )}

      {tab === 'matches' && (
        <Card>
          <CardHeader title="Pertandingan" subtitle="Hasil dicatat setelah bermain" />
          <EmptyState
            icon={<Trophy className="h-8 w-8" />}
            title="Belum ada pertandingan"
            description="Hasil pertandingan kegiatan ini akan muncul setelah dikirim."
          />
        </Card>
      )}

      {tab === 'leaderboard' && (
        <Card>
          <CardHeader title="Papan peringkat kategori" subtitle="Peringkat MMR" />
          {leaderboard.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : leaderboard.isError ? (
            <p className="flex items-center gap-2 text-sm text-ink-3">
              <Info className="h-4 w-4" /> Papan peringkat perlu masuk akun.
            </p>
          ) : leaderboard.data && leaderboard.data.length > 0 ? (
            <ol className="divide-y divide-line">
              {leaderboard.data.map((e) => (
                <li key={e.id} className="flex items-center gap-3 py-3">
                  <span className="w-8 text-center font-bold text-action">#{e.rank}</span>
                  <span className="min-w-0 flex-1 line-clamp-1 text-sm text-ink">
                    Peserta #{e.rank}
                  </span>
                  <span className="text-sm text-ink-3">{e.games_played} pertandingan</span>
                  <span className="font-semibold text-ink">{Math.round(e.rating)}</span>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState title="Belum ada peringkat" description="Main pertandingan untuk muncul di sini." />
          )}
        </Card>
      )}
    </div>
  );
}
