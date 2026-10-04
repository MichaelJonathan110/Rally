import { Link } from 'react-router-dom';
import { CalendarDays, MapPin, Users } from 'lucide-react';
import type { Activity } from '@/api/types';
import { cn } from '@/lib/utils';
import { formatCents } from '@/lib/utils';
import { dayLabel, clock, relative } from '@/lib/format';
import { categoryMeta, skillLabel, TONE } from '@/config/categories';
import { ActivityVisual } from '@/components/visuals/ActivityVisual';
import { RankBadge } from '@/components/RankBadge';
import { useActivityTypes } from '@/hooks/useCatalog';

/**
 * The signature activity card.
 *
 * Not a generic SaaS tile: a photograph of real people leads, the category
 * owns a pastel tone (chip + price + a tinted hairline), and the whole card
 * lifts on hover with a spring easing. Every card carries the same
 * information architecture but reads differently by category.
 */
export function ActivityCard({
  activity,
  className,
  variant = 'default',
}: {
  activity: Activity;
  className?: string;
  variant?: 'default' | 'compact';
}) {
  const meta = categoryMeta(activity.sport_category ?? activity.category);
  const tone = TONE[meta.tone];
  const spotsLeft = activity.max_participants - activity.participant_count;
  const full = spotsLeft <= 0;

  // Activity-type label (e.g. "Padel"). The card title is the venue name, so
  // the type is shown as its own chip - if the type clearly mismatches the
  // venue that is a data issue, surfaced here rather than hidden.
  const { data: types } = useActivityTypes();
  const typeLabel = activity.activity_type
    ? types?.find((x) => x.slug === activity.activity_type)?.label_id ?? activity.activity_type
    : null;
  const venueName = activity.venue?.name ?? null;

  if (variant === 'compact') {
    return (
      <Link
        to={`/activities/${activity.id}`}
        className={cn(
          'group flex items-center gap-3 rounded-xl border border-line bg-surface p-2.5 pr-4',
          'transition-all duration-300 hover:-translate-y-0.5 hover:shadow-soft',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action',
          className,
        )}
      >
        <ActivityVisual
          activity={activity}
          width={200}
          className="h-14 w-14 shrink-0"
          imgClassName="transition-transform duration-500 group-hover:scale-105"
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-ink">{activity.title}</p>
          <p className="mt-0.5 flex items-center gap-1.5 text-xs text-ink-3">
            <CalendarDays className="h-3.5 w-3.5" />
            {dayLabel(activity.starts_at)} · {clock(activity.starts_at)}
            {typeLabel ? (
              <>
                <span aria-hidden>·</span>
                <span className="font-semibold text-ink-2">{typeLabel}</span>
              </>
            ) : null}
          </p>
        </div>
        <span className="shrink-0 text-sm font-semibold text-ink">
          {formatCents(activity.cost_per_person_cents, activity.currency)}
        </span>
      </Link>
    );
  }

  return (
    <Link
      to={`/activities/${activity.id}`}
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-xl border border-line bg-surface shadow-soft',
        'transition-all duration-300 ease-spring hover:-translate-y-1.5 hover:shadow-lift',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action focus-visible:ring-offset-2 focus-visible:ring-offset-paper',
        className,
      )}
    >
      <div className="relative">
        <ActivityVisual
          activity={activity}
          width={800}
          className="aspect-[16/10] w-full"
          imgClassName="transition-transform duration-[900ms] ease-spring group-hover:scale-[1.06]"
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-ink/45 via-ink/5 to-transparent" />

        <div className="absolute inset-x-3 top-3 flex items-start justify-between gap-2">
          <span
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-2xs font-bold uppercase tracking-wide text-ink backdrop-blur-sm',
              tone.solid,
            )}
          >
            <span aria-hidden>{meta.emoji}</span>
            {meta.label}
          </span>
          <span className="rounded-full bg-surface/90 px-2.5 py-1 text-xs font-bold text-ink shadow-sm backdrop-blur-sm">
            {formatCents(activity.cost_per_person_cents, activity.currency)}
          </span>
        </div>

        {typeLabel ? (
          <div className="absolute inset-x-3 top-12 flex justify-start">
            <span className="inline-flex items-center gap-1 rounded-full border border-ink/10 bg-surface/92 px-2.5 py-1 text-2xs font-bold text-ink shadow-sm backdrop-blur-sm">
              <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-action" />
              {typeLabel}
            </span>
          </div>
        ) : null}

        <div className="absolute inset-x-3 bottom-3 flex items-center justify-between gap-2">
          <span className="rounded-full bg-ink/70 px-2.5 py-1 text-2xs font-semibold text-ink-inv backdrop-blur-sm">
            {relative(activity.starts_at)}
          </span>
          {full ? (
            <span className="rounded-full bg-danger px-2.5 py-1 text-2xs font-bold text-ink-inv">
              Penuh
            </span>
          ) : spotsLeft <= 3 ? (
            <span className="rounded-full bg-warning px-2.5 py-1 text-2xs font-bold text-ink">
              Sisa {spotsLeft}
            </span>
          ) : null}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-pretty font-display text-lg font-bold leading-snug tracking-tight text-ink">
              {activity.title}
            </h3>
            {venueName && venueName !== activity.title ? (
              <p className="mt-0.5 flex items-center gap-1 text-xs text-ink-3">
                <MapPin className="h-3 w-3 shrink-0" />
                <span className="truncate">{venueName}</span>
              </p>
            ) : null}
          </div>
        </div>

        <dl className="mt-auto space-y-2 text-sm text-ink-2">
          <div className="flex items-center gap-2">
            <dt className="sr-only">Jadwal</dt>
            <CalendarDays className="h-4 w-4 shrink-0 text-ink-3" />
            <dd className="truncate font-medium text-ink">
              {dayLabel(activity.starts_at)}
              <span className="font-normal text-ink-3"> · {clock(activity.starts_at)}</span>
            </dd>
          </div>
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <dt className="sr-only">Peserta</dt>
              <Users className="h-4 w-4 shrink-0 text-ink-3" />
              <dd>
                <span className="font-semibold text-ink">{activity.participant_count}</span>
                <span className="text-ink-3">/{activity.max_participants} peserta</span>
              </dd>
            </div>
            <RankBadge rating={1200 + activity.participant_count * 25} showRating={false} />
          </div>
        </dl>

        <div className="flex items-center gap-2 border-t border-line pt-3">
          <MapPin className="h-3.5 w-3.5 shrink-0 text-ink-3" />
          <span className="truncate text-xs text-ink-3">{skillLabel(activity.skill_level)}</span>
          <span className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-action opacity-0 transition-opacity group-hover:opacity-100">
            Lihat detail
          </span>
        </div>
      </div>
    </Link>
  );
}
