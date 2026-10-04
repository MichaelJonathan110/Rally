import { Link, useParams } from 'react-router-dom';
import { Users, LogOut, UserPlus } from 'lucide-react';
import { useClub, useClubMembers, useJoinClub, useLeaveClub } from '@/hooks/useClubs';
import { useAuth } from '@/hooks/useAuth';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader } from '@/components/ui/Card';
import { Avatar } from '@/components/ui/Avatar';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { cleanDescription } from '@/lib/format';

export default function ClubDetail() {
  const { id = '' } = useParams();
  const { user } = useAuth();
  const club = useClub(id);
  const members = useClubMembers(id);
  const join = useJoinClub(id);
  const leave = useLeaveClub(id);

  if (club.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }
  if (club.isError || !club.data) {
    return <ErrorState title="Komunitas tidak ditemukan" onRetry={() => club.refetch()} />;
  }

  const c = club.data;
  const isMember = members.data?.some((m) => m.user_id === user?.id && m.is_active);

  return (
    <div className="space-y-5">
      <Link to="/clubs" className="text-sm text-ink-3 hover:text-action">
        &larr; Semua komunitas
      </Link>
      <div className="card space-y-3 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="text-2xl font-bold text-ink">{c.name}</h1>
          <Badge tone="accent">{c.category}</Badge>
        </div>
        <p className="flex items-center gap-2 text-sm text-ink-2">
          <Users className="h-4 w-4" /> {c.member_count} anggota{c.city ? ` · ${c.city}` : ''}
        </p>
        {cleanDescription(c.description, c.name) ? (
          <p className="text-sm text-ink-3">{cleanDescription(c.description, c.name)}</p>
        ) : null}
        <div className="pt-1">
          {!user ? (
            <Link to="/login">
              <Button>Masuk untuk gabung</Button>
            </Link>
          ) : isMember ? (
            <Button variant="outline" loading={leave.isPending} onClick={() => leave.mutate()}>
              <LogOut className="h-4 w-4" /> Keluar komunitas
            </Button>
          ) : (
            <Button loading={join.isPending} onClick={() => join.mutate()}>
              <UserPlus className="h-4 w-4" /> Gabung komunitas
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader title="Anggota" subtitle={`${c.member_count} total`} />
        {members.isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : members.data && members.data.length > 0 ? (
          <ul className="divide-y divide-line">
            {members.data.map((m) => (
              <li key={m.id} className="flex items-center gap-3 py-3">
                <Avatar name={m.user_id.slice(0, 2).toUpperCase()} size={36} />
                <span className="min-w-0 flex-1 line-clamp-1 text-sm text-ink">
                  {m.user_id === user?.id ? 'Kamu' : `Anggota ${m.user_id.slice(0, 8)}`}
                </span>
                <Badge tone="neutral">{m.role}</Badge>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="Belum ada anggota" description="Jadilah yang pertama bergabung." />
        )}
      </Card>
    </div>
  );
}
