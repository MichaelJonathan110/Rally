import { useId } from 'react';
import { brand } from '../../config/brand';

type LogoVariant = 'mark' | 'wordmark' | 'full';
type LogoTone = 'ink' | 'action' | 'surface' | 'current';

export interface LogoProps {
  /** mark = badge only, wordmark = text only, full = badge + text */
  variant?: LogoVariant;
  /** px size of the square mark */
  size?: number;
  tone?: LogoTone;
  className?: string;
  /** Accessible label; pass '' to render decorative (aria-hidden). */
  title?: string;
}

const TONE_FILL: Record<LogoTone, string> = {
  ink: '#141414',
  action: '#FF6F55',
  surface: '#FFFFFF',
  current: 'currentColor',
};

/**
 * RALLY logo — ORIGINAL artwork (no third-party brand assets).
 *
 * Concept: the mark is a bold "R" whose diagonal leg is replaced by a
 * forward-leaning speed chevron, set inside a soft "court" tile. The
 * chevron reads as motion / a rally / a finish flag. Wordmark is a heavy
 * geometric sans with tight tracking.
 */
export function LogoMark({
  size = 32,
  tone = 'ink',
  className,
  title,
}: Omit<LogoProps, 'variant'>) {
  const gid = useId().replace(/:/g, '');
  const fill = TONE_FILL[tone];
  const decorative = title === '';
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      role={decorative ? undefined : 'img'}
      aria-hidden={decorative || undefined}
      aria-label={decorative ? undefined : title ?? `${brand.name} logo`}
      className={className}
    >
      {!decorative && title !== undefined ? <title>{title}</title> : null}
      <defs>
        <linearGradient id={`rm-${gid}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#FF6F55" />
          <stop offset="100%" stopColor="#FF9C86" />
        </linearGradient>
      </defs>
      {/* court tile */}
      <rect x="2" y="2" width="44" height="44" rx="13" fill={tone === 'current' ? 'none' : fill} opacity={tone === 'current' ? 1 : 0.08} />
      <rect x="2" y="2" width="44" height="44" rx="13" stroke={fill} strokeOpacity="0.18" strokeWidth="1.5" />
      {/* the R stem + bowl */}
      <path
        d="M16 35V13h9.2c4.6 0 7.8 2.7 7.8 7.1 0 3.1-1.5 5.3-4.2 6.3L34.5 35h-6.1l-4.6-7.6h-2.2V35H16Zm5.6-12.2h3.1c1.9 0 3-.9 3-2.6s-1.1-2.6-3-2.6h-3.1v5.2Z"
        fill={tone === 'current' ? 'currentColor' : fill}
      />
      {/* speed chevron replacing the leg */}
      <path d="M24.4 35l6.2-9.6 3.4 2.1-4.2 7.5h-5.4Z" fill={`url(#rm-${gid})`} />
      <path d="M30.6 25.4l3.3-5.1 3.2 2-3.1 5.2-3.4-2.1Z" fill={`url(#rm-${gid})`} opacity="0.75" />
    </svg>
  );
}

export function LogoWordmark({
  size = 22,
  tone = 'ink',
  className,
}: Omit<LogoProps, 'variant'>) {
  return (
    <span
      className={className}
      style={{
        fontFamily: 'Sora, ui-sans-serif, system-ui, sans-serif',
        fontWeight: 800,
        fontSize: size,
        letterSpacing: '0.14em',
        lineHeight: 1,
        color: TONE_FILL[tone],
      }}
    >
      {brand.name}
    </span>
  );
}

export default function Logo({
  variant = 'full',
  size = 32,
  tone = 'ink',
  className,
  title,
}: LogoProps) {
  if (variant === 'mark') {
    return <LogoMark size={size} tone={tone} className={className} title={title} />;
  }
  if (variant === 'wordmark') {
    return <LogoWordmark size={size * 0.72} tone={tone} className={className} />;
  }
  return (
    <span className={`inline-flex items-center gap-2.5 ${className ?? ''}`}>
      <LogoMark size={size} tone={tone} title={title} />
      <LogoWordmark size={size * 0.68} tone={tone} />
    </span>
  );
}
