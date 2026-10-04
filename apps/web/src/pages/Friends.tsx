import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, UserPlus, Check, MapPin, Trophy } from 'lucide-react';
import { useFollowSuggestions, useMyFollowing, useMyFriends, useFollowAction } from '@/hooks/useFollows';
import type { FollowUser } from '@/api/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/Avatar';
import { Tabs } from '@/components/ui/Tabs';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { RankBadge } from '@/components/RankBadge';
import { categoryMeta } from '@/config/categories';
import { cn } from '@/lib/utils';

type TabId = 'saran' | 'mengikuti' | 'teman';

function UserCard({ user }: { user: FollowUser }) {
  const follow = useFollowAction();
  const meta = categoryMeta(user.category ?? 'other');
  const busy = follow.isPending && follow.variables?.id === user.user_id;
  const following = follow.isPending && follow.variables?.id === user.user_id
    ? follow.variables.following
    : user.is_following;

  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-start gap-3">
        <Avatar name={user.display_name} src={user.avatar_url} size={48} />
        <div className="min-w-0 flex-1">
          <Link
            to={`/people`}
            className="block truncate font-semibold text-ink hover:underline"
          >
            {user.display_name}
          </Link>
          <p className="truncate text-sm text-ink-3">@{user.username}</p>
          {user.city ? (
            <p className="mt-0.5 flex items-center gap-1 text-xs text-ink-3">
              <MapPin className="h-3 w-3 shrink-0" />
              {user.city}
            </p>
          ) : null}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="neutral">
          {meta.emoji} {meta.label}
        </Badge>
        <RankBadge rating={user.rating} />
      </div>

      <p className="flex items-center gap-1.5 text-xs text-ink-3">
        <Trophy className="h-3.5 w-3.5" />
        {user.games_played} pertandingan
      </p>

      <Button
        variant={following ? 'outline' : 'primary'}
        size="sm"
        loading={busy}
        onClick={() => follow.mutate({ id: user.user_id, following })}
        className="mt-auto w-full"
      >
        {!busy && (following ? <Check className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />)}
        {following ? 'Mengikuti' : 'Ikuti'}
      </Button>
    </Card>
  );
}

function TabPanel({
  query,
  emptyTitle,
  emptyDesc,
}: {
  query: { data?: { items: FollowUser[] }; isLoading: boolean; isError: boolean };
  emptyTitle: string;
  emptyDesc: string;
}) {
  if (query.isLoading) return <SkeletonList count={6} />;
  const items = query.data?.items ?? [];
  if (query.isError || items.length === 0) {
    return (
      <EmptyState
        icon={<Users className="h-8 w-8" />}
        title={emptyTitle}
        description={emptyDesc}
      />
    );
  }
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((u) => (
        <UserCard key={u.user_id} user={u} />
      ))}
    </div>
  );
}

export default function Friends() {
  const [tab, setTab] = useState<TabId>('saran');
  const suggestions = useFollowSuggestions(12);
  const following = useMyFollowing();
  const friends = useMyFriends();

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Sosial"
        title="Teman & Mengikuti"
        subtitle="Temukan pemain lain, ikuti mereka, dan pantau teman sesama olahraga."
      />

      <Tabs
        items={[
          { id: 'saran', label: 'Saran', badge: suggestions.data?.items.length },
          { id: 'mengikuti', label: 'Mengikuti', badge: following.data?.items.length },
          { id: 'teman', label: 'Teman', badge: friends.data?.items.length },
        ]}
        value={tab}
        onChange={(id) => setTab(id as TabId)}
      />

      <div className={cn('pt-1')}>
        {tab === 'saran' ? (
          <TabPanel
            query={suggestions}
            emptyTitle="Belum ada saran"
            emptyDesc="Mainkan lebih banyak pertandingan untuk mendapat rekomendasi teman."
          />
        ) : tab === 'mengikuti' ? (
          <TabPanel
            query={following}
            emptyTitle="Belum mengikuti siapa pun"
            emptyDesc="Mulai ikuti pemain dari tab Saran untuk melihat aktivitas mereka."
          />
        ) : (
          <TabPanel
            query={friends}
            emptyTitle="Belum ada teman"
            emptyDesc="Ikuti pemain lain dan bertanding bersama untuk menjadi teman."
          />
        )}
      </div>
    </div>
  );
}
