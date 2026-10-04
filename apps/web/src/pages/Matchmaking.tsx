import { Link } from 'react-router-dom';
import { CalendarCheck, MapPin, Sparkles, Users } from 'lucide-react';
import { useMatchmaking } from '@/hooks/useDiscovery';
import { useAuth } from '@/hooks/useAuth';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Reveal } from '@/components/motion/Reveal';
import { categoryMeta } from '@/config/categories';
import { dayLabel, clock } from '@/lib/format';
import { formatCents, initials } from '@/lib/utils';

export default function Matchmaking() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useMatchmaking(8);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Untukmu"
        title="Cocok Untukmu"
        subtitle="Rekomendasi kegiatan dan partner dari minat, kota, dan MMR kamu."
      />

      {!user ? (
        <EmptyState
          icon={<Sparkles className="h-8 w-8" />}
          title="Masuk untuk melihat rekomendasi"
          description="Rekomendasi kegiatan dan partner dipersonalisasi dari minat, kota, dan MMR kamu."
          action={
            <Link to="/login" className="font-medium text-action hover:underline">
              Masuk
            </Link>
          }
        />
      ) : isLoading ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-40 rounded-xl" />
            ))}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
        </div>
      ) : isError || !data ? (
        <EmptyState
          icon={<Sparkles className="h-8 w-8" />}
          title="Belum bisa memuat rekomendasi"
          description="Coba muat ulang halaman sebentar lagi."
        />
      ) : (
        <>
          <section className="space-y-4">
            <h2 className="font-display text-xl font-bold text-ink">Kegiatan Untukmu</h2>
            {data.activities.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.activities.map((a, i) => {
                  const meta = categoryMeta(a.category);
                  return (
                    <Reveal key={a.id} delay={i * 50}>
                      <Link to={`/activities/${a.id}`} className="card block h-full p-4 hover:border-action/40">
                        <div className="flex items-start gap-3">
                          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-paper-warm text-lg" aria-hidden>
                            {meta.emoji}
                          </span>
                          <div className="min-w-0 flex-1">
                            <h3 className="line-clamp-2 font-semibold text-ink">{a.title}</h3>
                            <p className="mt-0.5 text-xs text-ink-3">{meta.label}</p>
                          </div>
                        </div>
                        {a.reason ? (
                          <p className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-action/10 px-2.5 py-0.5 text-xs font-medium text-action">
                            <Sparkles className="h-3 w-3" />
                            {a.reason}
                          </p>
                        ) : null}
                        <p className="mt-3 flex items-center gap-1.5 text-sm text-ink-3">
                          <MapPin className="h-4 w-4" />
                          {a.venue_name ? `${a.venue_name} · ` : ''}
                          {a.city ?? 'Lokasi menyusul'}
                        </p>
                        <div className="mt-2 flex items-center justify-between gap-2 text-xs text-ink-3">
                          <span className="inline-flex items-center gap-1">
                            <CalendarCheck className="h-3.5 w-3.5" />
                            {dayLabel(a.starts_at)} · {clock(a.starts_at)}
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <Users className="h-3.5 w-3.5" />
                            {a.participant_count}/{a.max_participants}
                          </span>
                        </div>
                        <p className="mt-3 text-sm font-semibold text-ink">
                          {formatCents(a.cost_per_person_cents, a.currency)}
                        </p>
                      </Link>
                    </Reveal>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={<CalendarCheck className="h-8 w-8" />}
                title="Belum ada kegiatan yang cocok"
                description="Ikuti beberapa kegiatan untuk menyempurnakan rekomendasimu."
              />
            )}
          </section>

          <section className="space-y-4">
            <h2 className="font-display text-xl font-bold text-ink">Partner Latihan</h2>
            {data.partners.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {data.partners.map((p, i) => (
                  <Reveal key={p.user_id} delay={i * 50}>
                    <Card className="flex items-start gap-3">
                      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-action/10 text-sm font-semibold text-action">
                        {initials(p.display_name)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="truncate font-semibold text-ink">{p.display_name}</h3>
                          <Badge tone={p.rating ? 'accent' : 'neutral'}>
                            {p.rating ? Math.round(p.rating) : 'UNRANKED'}
                          </Badge>
                        </div>
                        <p className="mt-0.5 flex items-center gap-1.5 text-sm text-ink-3">
                          <MapPin className="h-4 w-4" />
                          {p.city ?? 'Kota belum diisi'}
                        </p>
                        {p.shared_categories.length > 0 ? (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {p.shared_categories.map((c) => (
                              <span key={c} className="rounded-full bg-ink/[0.06] px-2 py-0.5 text-2xs font-medium text-ink-2">
                                {categoryMeta(c).emoji} {categoryMeta(c).label}
                              </span>
                            ))}
                          </div>
                        ) : null}
                        <p className="mt-2 text-xs text-ink-3">
                          {p.games_played} pertandingan · {categoryMeta(p.category).label}
                        </p>
                      </div>
                    </Card>
                  </Reveal>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<Users className="h-8 w-8" />}
                title="Belum ada partner yang cocok"
                description="Tambahkan minat dan main pertandingan untuk menemukan partner."
              />
            )}
          </section>
        </>
      )}
    </div>
  );
}
