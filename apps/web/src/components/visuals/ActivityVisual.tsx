import { useState, type ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { activityGradient, activityImage, categoryCover, categoryGradient } from '@/lib/imagery';
import { categoryMeta } from '@/config/categories';

type Shape = 'card' | 'hero' | 'banner' | 'blob';

const SHAPE: Record<Shape, string> = {
  card: 'rounded-[1.75rem]',
  hero: 'rounded-[2.25rem]',
  banner: 'rounded-[2rem]',
  blob: 'rounded-[58%_42%_45%_55%/48%_52%_48%_52%]',
};

export function ActivityVisual({
  activity,
  shape = 'card',
  width = 1200,
  className,
  imgClassName,
  alt,
  priority = false,
  children,
}: {
  activity: { id: string; category: string | null | undefined; title: string; activity_type?: string | null };
  shape?: Shape;
  width?: number;
  className?: string;
  imgClassName?: string;
  alt?: string;
  priority?: boolean;
  children?: ReactNode;
}) {
  const [failed, setFailed] = useState(false);
  const meta = categoryMeta(activity.category);
  const gradient = activityGradient(activity);
  const src = activityImage(activity, width);

  return (
    <div
      className={cn('relative isolate overflow-hidden', SHAPE[shape], className)}
      style={{ backgroundImage: gradient }}
    >
      {!failed ? (
        <img
          src={src}
          alt={alt ?? meta.label + ': ' + activity.title}
          loading={priority ? 'eager' : 'lazy'}
          decoding="async"
          onError={() => setFailed(true)}
          className={cn('h-full w-full object-cover', imgClassName)}
        />
      ) : (
        <div className="flex h-full w-full items-end justify-start p-4" aria-hidden>
          <span className="text-5xl drop-shadow-sm">{meta.emoji}</span>
        </div>
      )}
      {children}
    </div>
  );
}

export function CategoryVisual({
  category,
  shape = 'banner',
  width = 1200,
  className,
  imgClassName,
  alt,
  children,
}: {
  category: string | null | undefined;
  shape?: Shape;
  width?: number;
  className?: string;
  imgClassName?: string;
  alt?: string;
  children?: ReactNode;
}) {
  const [failed, setFailed] = useState(false);
  const meta = categoryMeta(category);
  return (
    <div
      className={cn('relative isolate overflow-hidden', SHAPE[shape], className)}
      style={{ backgroundImage: categoryGradient(category) }}
    >
      {!failed ? (
        <img
          src={categoryCover(category, width)}
          alt={alt ?? meta.label}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
          className={cn('h-full w-full object-cover', imgClassName)}
        />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-4xl" aria-hidden>
          {meta.emoji}
        </div>
      )}
      {children}
    </div>
  );
}
