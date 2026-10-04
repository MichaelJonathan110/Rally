import { Link } from 'react-router-dom';
import {
  Award,
  Flame,
  Trophy,
  CalendarCheck,
  Star,
  Users,
  Swords,
  Target,
  Zap,
  Shield,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { useUserProgress } from '@/hooks/useDiscovery';
import { useAuth } from '@/hooks/useAuth';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Reveal } from '@/components/motion/Reveal';
import { cn } from '@/lib/utils';

const ICONS: Record<string, LucideIcon> = {
  flame: Flame,
  streak: Flame,
  trophy: Trophy,
  calendar: CalendarCheck,
  star: Star,
  users: Users,
  team: Users,
  swords: Swords,
  match: Swords,
  target: Target,
  zap: Zap,
  shield: Shield,
  sparkles: Sparkles,
};

function iconFor(code: string | null | undefined): LucideIcon {
  const key = (code ?? '').toLowerCase();
  for (const k of Object.keys(ICONS)) {
    if (key.includes(k)) return ICONS[k];
  }
  return Award;
}

export default function Achievements() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useUserProgress(user?.id);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Progres"
        title="Pencapaian"
        subtitle="Streak dan lencana kamu."
      />

      {!user ? (
        <EmptyState
          icon={<Award className="h-8 w-8" />}
          title="Masuk untuk melihat pencapaianmu"
          description="Streak dan lencana hanya tersedia untuk akun yang sudah masuk."
          action={
            <Link to="/login" className="font-medium text-action hover:underline">
              Masuk
            </Link>
          }
        />
      ) : isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-40 rounded-xl" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" />
            ))}
          </div>
        </div>
      ) : isError || !data ? (
        <EmptyState
          icon={<Award className="h-8 w-8" />}
          title="Belum bisa memuat pencapaian"
          description="Coba muat ulang halaman sebentar lagi."
        />
      ) : (
        <>
          <Card className="relative overflow-hidden bg-ink text-ink-inv">
            <div
              className="absolute -right-10 -top-10 h-40 w-40 rounded-full opacity-30"
              style={{ backgroundImage: 'radial-gradient(circle,#FF6F55 0%,transparent 70%)' }}
              aria-hidden
            />
            <div className="relative flex flex-wrap items-center gap-6">
              <div className="flex items-center gap-4">
                <span className="grid h-16 w-16 place-items-center rounded-2xl bg-action text-ink">
                  <Flame className="h-8 w-8" />
                </span>
                <div>
                  <p className="text-2xs font-semibold uppercase tracking-[0.16em] text-ink-inv/60">
                    Streak saat ini
                  </p>
                  <p className="font-display text-4xl font-extrabold tabular-nums">
                    {data.current_streak}
                    <span className="ml-1 text-lg text-ink-inv/70">hari</span>
                  </p>
                </div>
              </div>
              <dl className="flex flex-wrap gap-x-8 gap-y-3">
                <div>
                  <dt className="text-2xs font-semibold uppercase tracking-wide text-ink-inv/60">
                    Streak terpanjang
                  </dt>
                  <dd className="font-display text-2xl font-extrabold tabular-nums">
                    {data.longest_streak}
                  </dd>
                </div>
                <div>
                  <dt className="text-2xs font-semibold uppercase tracking-wide text-ink-inv/60">
                    Hari aktif
                  </dt>
                  <dd className="font-display text-2xl font-extrabold tabular-nums">
                    {data.total_active_days}
                  </dd>
                </div>
              </dl>
            </div>
          </Card>

          {data.weekly.length > 0 ? (
            <Card>
              <CardHeader title="Aktivitas mingguan" subtitle="Jumlah kegiatan per minggu" />
              <div className="flex items-end gap-3">
                {data.weekly.map((w) => {
                  const max = Math.max(...data.weekly.map((x) => x.count), 1);
                  const h = Math.round((w.count / max) * 100);
                  return (
                    <div key={w.week_start} className="flex flex-1 flex-col items-center gap-2">
                      <span className="text-xs font-semibold text-ink-2 tabular-nums">{w.count}</span>
                      <div className="flex h-32 w-full items-end">
                        <div
                          className="w-full rounded-t-lg bg-gradient-to-t from-cyan to-mint"
                          style={{ height: `${Math.max(h, 4)}%` }}
                          aria-hidden
                        />
                      </div>
                      <span className="text-2xs text-ink-3">{w.week_start.slice(5, 10)}</span>
                    </div>
                  );
                })}
              </div>
            </Card>
          ) : null}

          <section className="space-y-4">
            <h2 className="font-display text-xl font-bold text-ink">Lencana</h2>
            {data.achievements.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.achievements.map((ach, i) => {
                  const Icon = iconFor(ach.code);
                  const pct = ach.target > 0 ? Math.min(100, (ach.progress / ach.target) * 100) : 0;
                  return (
                    <Reveal key={ach.code} delay={i * 40}>
                      <Card className={cn('flex h-full flex-col', ach.earned && 'border-action/40')}>
                        <div className="flex items-start gap-3">
                          <span
                            className={cn(
                              'grid h-11 w-11 shrink-0 place-items-center rounded-xl',
                              ach.earned ? 'bg-action text-ink' : 'bg-ink/[0.06] text-ink-3',
                            )}
                          >
                            <Icon className="h-5 w-5" />
                          </span>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-start justify-between gap-2">
                              <h3 className="font-semibold text-ink">{ach.name}</h3>
                              {ach.earned ? <Badge tone="success">Diraih</Badge> : null}
                            </div>
                            {ach.description ? (
                              <p className="mt-0.5 text-sm text-ink-3">{ach.description}</p>
                            ) : null}
                          </div>
                        </div>
                        <div className="mt-auto pt-4">
                          <div className="h-2 overflow-hidden rounded-full bg-ink/[0.06]">
                            <div
                              className={cn(
                                'h-full rounded-full transition-all duration-700 ease-spring',
                                ach.earned ? 'bg-action' : 'bg-cyan',
                              )}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <div className="mt-1.5 flex items-center justify-between text-xs text-ink-3">
                            <span>
                              {ach.progress}/{ach.target}
                            </span>
                            <span className="inline-flex items-center gap-1 font-medium text-warning">
                              <Star className="h-3 w-3" />
                              {ach.points} poin
                            </span>
                          </div>
                        </div>
                      </Card>
                    </Reveal>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={<Award className="h-8 w-8" />}
                title="Belum ada lencana"
                description="Ikuti kegiatan dan pertandingan untuk membuka lencana pertamamu."
              />
            )}
          </section>
        </>
      )}
    </div>
  );
}
