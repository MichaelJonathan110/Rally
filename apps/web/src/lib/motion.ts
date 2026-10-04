/**
 * Motion + performance tier hooks.
 *
 * Motion in RALLY is intentional and always subordinate to usability: every
 * effect degrades to a static presentation when the user asks for reduced
 * motion, and heavy visual work is skipped on low-performance devices.
 */
import { useEffect, useRef, useState } from 'react';

/** True when the user prefers reduced motion (SSR/jsdom safe). */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return reduced;
}

export type PerfTier = 'high' | 'medium' | 'low';

/**
 * Coarse device performance tier (HIGH / MEDIUM / LOW) used by the visual
 * layer to decide how much work to do. Falls back to MEDIUM when the signals
 * are unavailable (e.g. jsdom, old browsers).
 */
export function usePerformanceTier(): PerfTier {
  const [tier, setTier] = useState<PerfTier>('medium');
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const nav = navigator as Navigator & {
      deviceMemory?: number;
      hardwareConcurrency?: number;
      connection?: { saveData?: boolean };
    };
    const cores = nav.hardwareConcurrency ?? 4;
    const memory = nav.deviceMemory ?? 4;
    const saveData = Boolean(nav.connection?.saveData);
    let next: PerfTier = 'high';
    if (saveData || cores <= 2 || memory <= 2) next = 'low';
    else if (cores <= 4 || memory <= 4) next = 'medium';
    setTier(next);
  }, []);
  return tier;
}

/**
 * IntersectionObserver-driven "has this element entered the viewport once"
 * flag. Used for scroll reveals and for lazily mounting heavy visuals so the
 * initial paint stays fast.
 */
export function useInView<T extends HTMLElement = HTMLDivElement>(
  options: { rootMargin?: string; threshold?: number; once?: boolean } = {},
) {
  const { rootMargin = '0px 0px -10% 0px', threshold = 0.15, once = true } = options;
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setInView(true);
            if (once) observer.disconnect();
          } else if (!once) {
            setInView(false);
          }
        }
      },
      { rootMargin, threshold },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [rootMargin, threshold, once]);

  return { ref, inView };
}
