import { useEffect, useRef, useState } from 'react';
import { useInView, usePrefersReducedMotion } from '@/lib/motion';

/**
 * Animated number that counts up once it scrolls into view. With reduced
 * motion (or no rAF) it renders the final value immediately.
 */
export function CountUp({
  value,
  duration = 1100,
  format,
  className,
}: {
  value: number;
  duration?: number;
  format?: (n: number) => string;
  className?: string;
}) {
  const reduced = usePrefersReducedMotion();
  const { ref, inView } = useInView<HTMLSpanElement>();
  const [display, setDisplay] = useState(reduced ? value : 0);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    if (reduced) {
      setDisplay(value);
      return;
    }
    if (!inView) return;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (value - from) * eased);
      if (t < 1) frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
    return () => {
      if (frame.current) cancelAnimationFrame(frame.current);
    };
  }, [inView, reduced, value, duration]);

  const text = format ? format(display) : Math.round(display).toLocaleString('id-ID');
  return (
    <span ref={ref} className={className}>
      {text}
    </span>
  );
}
