import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Trophy, Star, LogOut, MapPin, Flame, Sparkles } from 'lucide-react';
import { useAuth, useLogout, useUpdateMe } from '@/hooks/useAuth';
import { useUserRatings } from '@/hooks/useRatings';
import { useMyBookings } from '@/hooks/useBookings';
import { useMyActivities } from '@/hooks/useActivities';
import { Button } from '@/components/ui/Button';
import { ImageUpload } from '@/components/ImageUpload';
import { Tabs } from '@/components/ui/Tabs';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ActivityCard } from '@/components/ActivityCard';
import { RankBadge, tierFor } from '@/components/RankBadge';
import { Reveal } from '@/components/motion/Reveal';
import { CountUp } from '@/components/motion/CountUp';
import { categoryMeta, skillLabel, TONE } from '@/config/categories';
import { relative } from '@/lib/format';

export default function Profile() {
  const { user } = useAuth();
  const logout = useLogout();
  const updateMe = useUpdateMe();
  const ratings = useUserRatings(user?.id);
  const bookings = useMyBookings();
  const mine = useMyActivities({ active_only: true, limit: 12 });
  const [tab, setTab] = useState('aktif');

  const list = ratings.data?.ratings ?? [];
  const games = useMemo(() => list.reduce((s, r) => s + r.games_played, 0), [list]);
  const top = useMemo(() => [...list].sort((a, b) => b.rating - a.rating)[0], [list]);
  const activeActivities = mine.data?.items ?? [];

  if (!user) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const p = user.profile;
  const displayName = p?.display_name || user.username;

  const achievements = [
    { id: 'first', label: 'Pertandingan pertama', ok: games > 0, icon: <Star className="h-5 w-5" /> },
    { id: 'regular', label: '5 pertandingan', ok: games >= 5, icon: <Flame className="h-5 w-5" /> },
    { id: 'booker', label: 'Booking pertama', ok: (bookings.data?.total ?? 0) > 0, icon: <Trophy className="h-5 w-5" /> },
    { id: 'verified', label: 'Terverifikasi', ok: user.is_verified, icon: <Sparkles className="h-5 w-5" /> },
    { id: 'competitor', label: '10 pertandingan', ok: games >= 10, icon: <Trophy className="h-5 w-5" /> },
    { id: 'host', label: 'Host kegiatan', ok: activeActivities.length > 0, icon: <Star className="h-5 w-5" /> },
  ];

  return (
    <div className="space-y-7">
      <section className="relative overflow-hidden rounded-2xl border border-line bg-surface shadow-soft">
        <div
          className="absolute inset-x-0 top-0 h-28"
          style={{ backgroundImage: 'linear-gradient(120deg,#DCF4F1 0%,#EFF9D6 60%,#FFE3DB 100%)' }}
          aria-hidden
        />
        <div className="relative flex flex-col items-start gap-5 p-5 pt-16 sm:flex-row sm:p-6 sm:pt-20">
          <div className="w-28 shrink-0">
            <ImageUpload
              purpose="avatar"
              shape="circle"
              value={p?.avatar_url}
              onChange={(url) => updateMe.mutate({ avatar_url: url })}
            />
            <p className="mt-1.5 text-center text-2xs font-semibold uppercase tracking-wide text-ink-3">
              {updateMe.isPending ? 'Menyimpan…' : 'Ganti foto'}
            </p>
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-2xl font-extrabold text-ink sm:text-3xl">
              {displayName}
            </h1>
            <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-3">
              <span className="inline-flex items-center gap-1.5">
                <Mail className="h-4 w-4" /> {user.email}
              </span>
              {p?.city ? (
                <span className="inline-flex items-center gap-1.5">
                  <MapPin className="h-4 w-4" /> {p.city}
                </span>
              ) : null}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="pill capitalize">{skillLabel(p?.skill_level)}</span>
              {user.is_verified ? (
                <span className="pill border-success/30 bg-success/10 text-success">Terverifikasi</span>
              ) : null}
              {top ? <RankBadge rating={top.rating} /> : null}
            </div>
            {p?.bio ? <p className="mt-3 max-w-2xl text-sm text-ink-2">{p.bio}</p> : null}
          </div>
          <Button variant="outline" onClick={logout}>
            <LogOut className="h-4 w-4" /> Keluar
          </Button>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: 'Reputasi', value: p?.reputation_score ?? 0 },
          { label: 'Kategori MMR', value: list.length },
          { label: 'Booking', value: bookings.data?.total ?? 0 },
          { label: 'Pertandingan', value: games },
        ].map((s) => (
          <div key={s.label} className="rounded-xl border border-line bg-surface p-4 shadow-soft">
            <p className="text-2xs font-semibold uppercase tracking-[0.14em] text-ink-3">
              {s.label}
            </p>
            <p className="mt-1 font-display text-3xl font-extrabold text-ink">
              <CountUp value={s.value} />
            </p>
          </div>
        ))}
      </section>

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          { value: 'aktif', label: 'Kegiatan aktif' },
          { value: 'mmr', label: 'MMR' },
          { value: 'lencana', label: 'Lencana' },
        ]}
      />

      {tab === 'aktif' ? (
        mine.isLoading ? (
          <Skeleton className="h-48 w-full" />
        ) : activeActivities.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {activeActivities.map((a, i) => (
              <Reveal key={a.id} delay={i * 50}>
                <ActivityCard activity={a} className="h-full" />
              </Reveal>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<Sparkles className="h-8 w-8" />}
            title="Belum ada kegiatan aktif"
            description="Ikut kegiatan dari halaman Jelajah atau buat milikmu sendiri."
            action={
              <Link to="/discover">
                <Button>Jelajahi kegiatan</Button>
              </Link>
            }
          />
        )
      ) : null}

      {tab === 'mmr' ? (
        ratings.isLoading ? (
          <Skeleton className="h-40 w-full" />
        ) : list.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {list.map((r) => {
              const meta = categoryMeta(r.category);
              const tone = TONE[meta.tone];
              const pct = Math.min(100, Math.max(4, ((r.rating - 1000) / 700) * 100));
              return (
                <div key={r.id} className="rounded-xl border border-line bg-surface p-4 shadow-soft">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`grid h-9 w-9 place-items-center rounded-lg text-lg ${tone.solid}`} aria-hidden>
                        {meta.emoji}
                      </span>
                      <div>
                        <p className="text-sm font-bold text-ink">{meta.label}</p>
                        <p className="text-xs text-ink-3">
                          {r.wins}M · {r.losses}K · {r.draws}S
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-display text-2xl font-extrabold tabular-nums text-ink">
                        {Math.round(r.rating)}
                      </p>
                      <p className="text-2xs font-semibold uppercase tracking-wide text-ink-3">
                        {tierFor(r.rating).label}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-ink/[0.06]">
                    <div className="h-full rounded-full bg-action" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={<Star className="h-8 w-8" />}
            title="Belum ada peringkat MMR"
            description="Ikut kegiatan ber-MMR dan selesaikan pertandingan untuk membuka peringkatmu."
          />
        )
      ) : null}

      {tab === 'lencana' ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {achievements.map((a) => (
            <div
              key={a.id}
              className={
                a.ok
                  ? 'flex flex-col items-center gap-2 rounded-xl border border-action/30 bg-action/5 p-4 text-center'
                  : 'flex flex-col items-center gap-2 rounded-xl border border-line bg-surface p-4 text-center opacity-55'
              }
            >
              <span className={a.ok ? 'text-action' : 'text-ink-3'}>{a.icon}</span>
              <p className="text-sm font-semibold text-ink">{a.label}</p>
              <p className="text-2xs font-semibold uppercase tracking-wide text-ink-3">
                {a.ok ? 'Terbuka' : 'Terkunci'}
              </p>
            </div>
          ))}
        </div>
      ) : null}

      {activeActivities.length > 0 ? (
        <p className="text-center text-xs text-ink-3">
          Kegiatan terdekat: {relative(activeActivities[0].starts_at)}
        </p>
      ) : null}
    </div>
  );
}
