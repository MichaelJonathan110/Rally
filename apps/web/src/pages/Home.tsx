import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  MapPin,
  Sparkles,
  Users,
  Zap,
  CalendarCheck,
  Activity as ActivityIcon,
} from 'lucide-react';
import { useActivities } from '@/hooks/useActivities';
import { useVenues } from '@/hooks/useVenues';
import { useClubs } from '@/hooks/useClubs';
import { useAuthStore } from '@/store/auth';
import { ActivityCard } from '@/components/ActivityCard';
import { CategoryRail } from '@/components/CategoryRail';
import { MyActivitiesRail } from '@/components/MyActivitiesRail';
import { CategoryVisual } from '@/components/visuals/ActivityVisual';
import { Reveal } from '@/components/motion/Reveal';
import { CountUp } from '@/components/motion/CountUp';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { StatTile } from '@/components/ui/StatTile';
import { Skeleton } from '@/components/ui/Skeleton';
import { CityOnboarding } from '@/components/city/CityOnboarding';
import { useCityStore } from '@/store/city';
import { useT } from '@/i18n/strings';
import { categoryMeta, CATEGORIES, TONE } from '@/config/categories';
import { dayLabel, clock, relative } from '@/lib/format';
import { formatCents, cn } from '@/lib/utils';

function Hero() {
  const t = useT();
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const city = useCityStore((s) => s.city);
  const { data } = useActivities({ limit: 50, upcoming: true, city: city || undefined });
  const total = data?.total ?? 0;

  return (
    <section className="relative overflow-hidden rounded-2xl border border-line bg-surface shadow-soft">
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(120% 90% at 88% 8%, #DCF4F1 0%, transparent 55%), radial-gradient(90% 80% at 8% 100%, #EFF9D6 0%, transparent 55%), linear-gradient(180deg,#FFFFFF 0%,#FBF8F3 100%)',
        }}
        aria-hidden
      />
      <div className="relative p-6 sm:p-9 lg:p-12">
        <div className="max-w-2xl">
          <p className="eyebrow flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5" />
            {t('hero.eyebrow')}
          </p>
          <h1 className="mt-3 text-balance font-display text-display font-extrabold text-ink">
            {user ? (
              <>
                Ayo gerak,
                <br />
                {(user.profile?.display_name ?? user.username).split(' ')[0]}.
              </>
            ) : (
              <>
                {t('hero.titleGuest1')}
                <br />
                {t('hero.titleGuest2')}
              </>
            )}
          </h1>
          <p className="mt-4 max-w-md text-pretty text-base text-ink-2 sm:text-lg">
            {t('hero.subtitleA')}{' '}
            <span className="font-semibold text-ink">
              <CountUp value={total} />
            </span>{' '}
            {t('hero.subtitleB')}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              to="/discover"
              className="group inline-flex h-12 items-center gap-2 rounded-full bg-action px-6 font-bold text-ink shadow-pop transition-all duration-200 ease-spring hover:-translate-y-0.5 hover:bg-action-dark"
            >
              {t('hero.ctaExplore')}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              to={token ? '/create' : '/register'}
              className="inline-flex h-12 items-center gap-2 rounded-full border border-line bg-surface px-6 font-semibold text-ink transition-colors hover:border-ink/25"
            >
              {token ? t('hero.ctaCreate') : t('hero.ctaJoin')}
            </Link>
          </div>

          <div className="mt-5 max-w-md">
            <CityOnboarding />
          </div>

          <dl className="mt-7 flex flex-wrap gap-x-7 gap-y-3">
            {[
              { k: t('hero.statActivities'), v: total },
              { k: t('hero.statCategories'), v: CATEGORIES.length },
            ].map((s) => (
              <div key={s.k}>
                <dt className="text-2xs font-semibold uppercase tracking-[0.14em] text-ink-3">
                  {s.k}
                </dt>
                <dd className="font-display text-2xl font-extrabold text-ink">
                  <CountUp value={s.v} />
                </dd>
              </div>
            ))}
          </dl>
        </div>

        
      </div>
    </section>
  );
}

function StatsStrip() {
  const activities = useActivities({ limit: 1, upcoming: true });
  const venues = useVenues({ limit: 100 });
  const clubs = useClubs({ limit: 1 });

  const cities = useMemo(() => {
    const set = new Set<string>();
    for (const v of venues.data?.items ?? []) if (v.city) set.add(v.city);
    return set.size;
  }, [venues.data]);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <StatTile
        label="Kegiatan"
        value={activities.data?.total ?? 0}
        tone="cyan"
        icon={<ActivityIcon className="h-4 w-4" />}
      />
      <StatTile
        label="Venue"
        value={venues.data?.total ?? 0}
        tone="mint"
        icon={<MapPin className="h-4 w-4" />}
      />
      <StatTile
        label="Komunitas"
        value={clubs.data?.total ?? 0}
        tone="lime"
        icon={<Users className="h-4 w-4" />}
      />
      <StatTile
        label="Kota"
        value={cities}
        tone="yellow"
        icon={<Zap className="h-4 w-4" />}
        hint="Seluruh Indonesia"
      />
    </div>
  );
}

function UpcomingRail() {
  const city = useCityStore((s) => s.city);
  const { data, isLoading } = useActivities({ limit: 6, upcoming: true, city: city || undefined });
  const items = data?.items ?? [];

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-72 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {items.map((a, i) => (
        <Reveal key={a.id} delay={i * 60}>
          <ActivityCard activity={a} className="h-full" />
        </Reveal>
      ))}
    </div>
  );
}

function CategoryShowcase() {
  const city = useCityStore((s) => s.city);
  const activities = useActivities({ limit: 50, upcoming: true, city: city || undefined });
  const items = activities.data?.items ?? [];

  const byCategory = useMemo(() => {
    const map = new Map<string, typeof items>();
    for (const c of CATEGORIES) map.set(c.id, []);
    for (const a of items) {
      const list = map.get(a.category);
      if (list) list.push(a);
    }
    return map;
  }, [items]);

  return (
    <div className="space-y-4">
      {CATEGORIES.map((c) => {
        const list = byCategory.get(c.id) ?? [];
        if (list.length === 0) return null;
        const tone = TONE[c.tone];
        return (
          <Reveal key={c.id}>
            <div className="overflow-hidden rounded-xl border border-line bg-surface">
              <div className="flex items-center gap-4 border-b border-line p-4">
                <CategoryVisual
                  category={c.id}
                  shape="card"
                  className="h-16 w-16 shrink-0 sm:h-20 sm:w-20"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn('grid h-6 w-6 place-items-center rounded-md text-sm', tone.solid)}
                      aria-hidden
                    >
                      {c.emoji}
                    </span>
                    <h3 className="font-display text-lg font-bold text-ink">{c.label}</h3>
                    <span className="rounded-full bg-ink/[0.06] px-2 py-0.5 text-2xs font-semibold text-ink-2">
                      {list.length} kegiatan
                    </span>
                  </div>
                  <p className="mt-0.5 text-sm text-ink-3">{c.blurb}</p>
                </div>
                <Link
                  to={`/discover?sport_category=${c.id}`}
                  className="hidden shrink-0 items-center gap-1 text-sm font-semibold text-action hover:underline sm:inline-flex"
                >
                  Semua
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
              <ul className="divide-y divide-line">
                {list.slice(0, 3).map((a) => (
                  <li key={a.id}>
                    <Link
                      to={`/activities/${a.id}`}
                      className="group flex items-center gap-4 p-3.5 transition-colors hover:bg-ink/[0.02]"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-ink group-hover:text-action">
                          {a.title}
                        </p>
                        <p className="mt-0.5 flex items-center gap-3 text-xs text-ink-3">
                          <span className="inline-flex items-center gap-1">
                            <CalendarCheck className="h-3.5 w-3.5" />
                            {dayLabel(a.starts_at)} · {clock(a.starts_at)}
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <Users className="h-3.5 w-3.5" />
                            {a.participant_count}/{a.max_participants}
                          </span>
                        </p>
                      </div>
                      <span className="shrink-0 text-sm font-semibold text-ink">
                        {formatCents(a.cost_per_person_cents, a.currency)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        );
      })}
    </div>
  );
}

function NearbyStrip() {
  const city = useCityStore((s) => s.city);
  const activities = useActivities({ limit: 50, upcoming: true, city: city || undefined });
  const items = (activities.data?.items ?? []).slice(0, 4);
  if (items.length === 0) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {items.map((a) => (
        <Link
          key={a.id}
          to={`/activities/${a.id}`}
          className="group flex items-center gap-3 rounded-xl border border-line bg-surface p-3 transition-all duration-300 ease-spring hover:-translate-y-0.5 hover:shadow-soft"
        >
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-paper-warm text-lg">
            {categoryMeta(a.category).emoji}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-ink group-hover:text-action">
              {a.title}
            </p>
            <p className="text-xs text-ink-3">
              {relative(a.starts_at)} · {formatCents(a.cost_per_person_cents, a.currency)}
            </p>
          </div>
          <ArrowRight className="h-4 w-4 shrink-0 text-ink-3 transition-transform group-hover:translate-x-0.5 group-hover:text-action" />
        </Link>
      ))}
    </div>
  );
}

export default function Home() {
  const token = useAuthStore((s) => s.accessToken);

  return (
    <div className="space-y-10 sm:space-y-14">
      <Hero />

      <Reveal as="section">
        <StatsStrip />
      </Reveal>

      <Reveal as="section" className="space-y-4">
        <SectionHeader
          eyebrow="Kategori"
          title="Mau bergerak apa hari ini?"
          subtitle="Setiap kategori punya kegiatan nyata di bawahnya."
        />
        <CategoryRail />
      </Reveal>

      {token ? (
        <Reveal as="section" className="space-y-4">
          <SectionHeader
            eyebrow="Aktivitas saya"
            title="Yang sedang kamu ikuti"
            action={
              <Link
                to="/profile"
                className="inline-flex items-center gap-1 text-sm font-semibold text-action hover:underline"
              >
                Semua
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            }
          />
          <MyActivitiesRail />
        </Reveal>
      ) : null}

      <Reveal as="section" className="space-y-4">
        <SectionHeader eyebrow="Terdekat" title="Segera dimulai" />
        <NearbyStrip />
      </Reveal>

      <Reveal as="section" className="space-y-4">
        <SectionHeader
          eyebrow="Kegiatan pilihan"
          title="Sedang ramai minggu ini"
          subtitle="Kegiatan yang paling banyak diminati komunitas."
          action={
            <Link
              to="/discover"
              className="inline-flex items-center gap-1 text-sm font-semibold text-action hover:underline"
            >
              Jelajahi semua
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
        <UpcomingRail />
      </Reveal>

      <Reveal as="section" className="space-y-4">
        <SectionHeader
          eyebrow="Jelajahi per kategori"
          title="Setiap kategori, kegiatan nyata"
          subtitle="Bukan sekadar label - ada kegiatan sungguhan di setiap kategori."
        />
        <CategoryShowcase />
      </Reveal>
    </div>
  );
}
