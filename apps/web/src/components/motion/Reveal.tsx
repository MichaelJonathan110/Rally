import { type ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { useInView, usePrefersReducedMotion } from '@/lib/motion';

/**
 * Scroll reveal. Content is visible immediately when reduced motion is on or
 * when IntersectionObserver is unavailable, so nothing is ever hidden from a
 * user who cannot or does not want the animation.
 */
export function Reveal({
  children,
  delay = 0,
  className,
  as: Tag = 'div',
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: 'div' | 'section' | 'li' | 'article';
}) {
  const reduced = usePrefersReducedMotion();
  const { ref, inView } = useInView<HTMLDivElement>();
  const shown = reduced || inView;

  return (
    <Tag
      ref={ref as never}
      style={reduced ? undefined : { transitionDelay: `${delay}ms` }}
      className={cn(
        'motion-safe:transition-all motion-safe:duration-700 motion-safe:ease-spring',
        shown ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0',
        className,
      )}
    >
      {children}
    </Tag>
  );
}
