import { cn } from '@/lib/utils';

export type MmrTier =
  | 'Unranked'
  | 'Bronze'
  | 'Silver'
  | 'Gold'
  | 'Platinum'
  | 'Diamond'
  | 'Master'
  | 'Grandmaster'
  | 'God';

type Ramp = {
  level: number;
  m1: string; m2: string; m3: string;
  f1: string; f2: string; f3: string;
  g1: string; g2: string; g3: string;
  glow: string;
  trim: string;
  pips: number;
};

const TIER: Record<MmrTier, Ramp> = {
  Unranked:    { level: -1, m1: '#B9BFC6', m2: '#6E757D', m3: '#33383E', f1: '#A7ADB4', f2: '#767D85', f3: '#3A3F45', g1: '#C9CFD6', g2: '#8A9098', g3: '#4A5058', glow: '#8A8F98', trim: '#454A51', pips: 0 },
  Bronze:      { level: 1, m1: '#E7B98A', m2: '#B87A45', m3: '#5E3414', f1: '#D79A63', f2: '#A9683A', f3: '#5A3018', g1: '#FFD9A8', g2: '#D89A5B', g3: '#7A4820', glow: '#C98A4A', trim: '#5A3418', pips: 2 },
  Silver:      { level: 2, m1: '#FFFFFF', m2: '#C4CEDA', m3: '#6B7885', f1: '#E8EEF5', f2: '#B4BFCC', f3: '#68737F', g1: '#FFFFFF', g2: '#C9D4E0', g3: '#7A8794', glow: '#B9C6D6', trim: '#5E6975', pips: 3 },
  Gold:        { level: 3, m1: '#FFF2B0', m2: '#F2C14E', m3: '#8A6110', f1: '#FFE28A', f2: '#E0A92F', f3: '#7A550E', g1: '#FFF6D6', g2: '#F2C14E', g3: '#8A6110', glow: '#FFC93C', trim: '#6E4B0E', pips: 4 },
  Platinum:    { level: 4, m1: '#E9FFFB', m2: '#8FD9D0', m3: '#256B66', f1: '#CFF2EE', f2: '#7FCFC6', f3: '#225E59', g1: '#F2FFFD', g2: '#7FE6DA', g3: '#2A857C', glow: '#5FE0D6', trim: '#1F5A56', pips: 5 },
  Diamond:     { level: 5, m1: '#F0FAFF', m2: '#8FC6F5', m3: '#274F80', f1: '#D6ECFF', f2: '#7FB6EE', f3: '#234C7B', g1: '#FFFFFF', g2: '#7FD3FF', g3: '#2A6CAF', glow: '#6FB6FF', trim: '#1E4270', pips: 6 },
  Master:      { level: 6, m1: '#F3E9FF', m2: '#A87BE0', m3: '#3F1D6E', f1: '#E3D2FB', f2: '#9B6BDB', f3: '#391A66', g1: '#F8F0FF', g2: '#B98CFF', g3: '#5B3499', glow: '#B07CFF', trim: '#371A63', pips: 7 },
  Grandmaster: { level: 7, m1: '#FFE2DC', m2: '#E23B2E', m3: '#5C0D0B', f1: '#F3B7AE', f2: '#C42A20', f3: '#4A0B09', g1: '#FFEDEA', g2: '#FF5A4A', g3: '#8E1A13', glow: '#FF5A4A', trim: '#4A0B0A', pips: 8 },
  God:         { level: 8, m1: '#FFFFFF', m2: '#F7D96A', m3: '#8F6508', f1: '#FFF6D0', f2: '#F3D255', f3: '#8A6108', g1: '#FFFFFF', g2: '#FFF0A8', g3: '#C79A28', glow: '#FFF2B0', trim: '#7A5606', pips: 9 },
};

const CUP_BOWL = 'M150 184 C150 276 192 338 256 360 C320 338 362 276 362 184 Z';
const CUP_STEM = 'M238 356 L274 356 L280 410 L232 410 Z';
const CUP_BASE = 'M198 410 L314 410 L330 448 L182 448 Z';
const HANDLE_L = 'M150 192 C96 196 86 262 136 292';
const HANDLE_R = 'M362 192 C416 196 426 262 376 292';
const CROWN = 'M192 134 L210 68 L230 112 L256 44 L282 112 L302 68 L320 134 Z';
const GEM = 'M256 228 L302 252 L302 292 L256 316 L210 292 L210 252 Z';
const BLADE = 'M256 36 L274 96 L274 322 L238 322 L238 96 Z';
const SPARK = 'M0 -38 L9 -9 L38 0 L9 9 L0 38 L-9 9 L-38 0 L-9 -9 Z';
const RAYS = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345];
const RIVETS: [number, number][] = [
  [206, 462],
  [256, 462],
  [306, 462],
];

export function MmrEmblem({
  className,
  title,
  tier = 'Unranked',
  stars,
}: {
  className?: string;
  title?: string;
  tier?: MmrTier;
  stars?: number;
}) {
  // Guard: unknown/absent tier must NEVER fall back to a ranked (Grandmaster) emblem.
  const t = TIER[tier] ?? TIER.Unranked;
  const lvl = t.level;
  const n = Math.max(1, Math.min(9, stars ?? t.pips));
  const u = `mmr-${tier}`;
  const gap = n >= 8 ? 16 : n >= 6 ? 20 : 22;
  const sc = 0.26;
  const xs = Array.from({ length: n }, (_, i) => 256 - ((n - 1) * gap) / 2 + i * gap);
  const hasBlades = lvl >= 2;
  const hasHalo = lvl >= 3;
  const hasRays = lvl >= 8;

  return (
    <svg
      viewBox='0 0 512 512'
      role='img'
      aria-label={title ?? `Lencana peringkat MMR RALLY - ${tier}`}
      className={cn('h-auto w-full select-none', className)}
    >
      <defs>
        <linearGradient id={`${u}-metal`} x1='0' y1='0' x2='0.35' y2='1'>
          <stop offset='0' stopColor={t.m1} />
          <stop offset='0.42' stopColor={t.m2} />
          <stop offset='0.56' stopColor={t.m1} />
          <stop offset='1' stopColor={t.m3} />
        </linearGradient>
        <linearGradient id={`${u}-metal2`} x1='0' y1='0' x2='0' y2='1'>
          <stop offset='0' stopColor={t.m1} />
          <stop offset='0.5' stopColor={t.m2} />
          <stop offset='1' stopColor={t.m3} />
        </linearGradient>
        <linearGradient id={`${u}-face`} x1='0.15' y1='0' x2='0.85' y2='1'>
          <stop offset='0' stopColor={t.f1} />
          <stop offset='0.55' stopColor={t.f2} />
          <stop offset='1' stopColor={t.f3} />
        </linearGradient>
        <linearGradient id={`${u}-blade`} x1='0' y1='0' x2='1' y2='0'>
          <stop offset='0' stopColor={t.m3} />
          <stop offset='0.5' stopColor={t.m1} />
          <stop offset='1' stopColor={t.m2} />
        </linearGradient>
        <linearGradient id={`${u}-gemA`} x1='0' y1='0' x2='1' y2='1'>
          <stop offset='0' stopColor={t.g1} />
          <stop offset='1' stopColor={t.g2} />
        </linearGradient>
        <linearGradient id={`${u}-gemB`} x1='1' y1='0' x2='0' y2='1'>
          <stop offset='0' stopColor={t.g2} />
          <stop offset='1' stopColor={t.g3} />
        </linearGradient>
        <radialGradient id={`${u}-core`} cx='0.38' cy='0.3' r='0.85'>
          <stop offset='0' stopColor='#FFFFFF' />
          <stop offset='0.45' stopColor={t.g1} />
          <stop offset='1' stopColor={t.g3} />
        </radialGradient>
        <filter id={`${u}-soft`} x='-40%' y='-40%' width='180%' height='180%'>
          <feGaussianBlur stdDeviation='24' />
        </filter>
        <filter id={`${u}-glow`} x='-40%' y='-40%' width='180%' height='180%'>
          <feGaussianBlur stdDeviation='10' result='b' />
          <feMerge>
            <feMergeNode in='b' />
            <feMergeNode in='SourceGraphic' />
          </feMerge>
        </filter>
        <clipPath id={`${u}-clip`}>
          <path d={CUP_BOWL} />
        </clipPath>
      </defs>

      {hasHalo ? (
        <ellipse
          cx='256'
          cy='280'
          rx='232'
          ry='244'
          fill={t.glow}
          opacity={lvl >= 7 ? 0.24 : 0.13}
          filter={`url(#${u}-soft)`}
        />
      ) : null}

      {hasRays ? (
        <g opacity='0.36' filter={`url(#${u}-glow)`}>
          {RAYS.map((d) => (
            <rect
              key={d}
              x='253'
              y='6'
              width='6'
              height='152'
              rx='3'
              fill={t.glow}
              transform={`rotate(${d} 256 280)`}
            />
          ))}
        </g>
      ) : null}

      {hasBlades ? (
        <g>
          {[38, -38].map((a) => (
            <g key={a} transform={`rotate(${a} 256 300)`}>
              <circle cx='256' cy='406' r='13' fill={`url(#${u}-metal2)`} stroke='#121317' strokeWidth='5' />
              <rect x='247' y='342' width='18' height='52' rx='5' fill={`url(#${u}-metal2)`} stroke='#121317' strokeWidth='4' />
              <rect x='212' y='322' width='88' height='20' rx='7' fill={`url(#${u}-metal)`} stroke='#121317' strokeWidth='4' />
              <path d={BLADE} fill={`url(#${u}-blade)`} stroke='#121317' strokeWidth='5' strokeLinejoin='miter' />
              <path d='M256 62 L266 100 L266 314 L246 314 L246 100 Z' fill='#FFFFFF' opacity='0.22' />
            </g>
          ))}
        </g>
      ) : null}

      <path d={HANDLE_L} fill='none' stroke='#121317' strokeWidth='30' strokeLinecap='round' />
      <path d={HANDLE_R} fill='none' stroke='#121317' strokeWidth='30' strokeLinecap='round' />
      <path d={HANDLE_L} fill='none' stroke={`url(#${u}-metal)`} strokeWidth='20' strokeLinecap='round' />
      <path d={HANDLE_R} fill='none' stroke={`url(#${u}-metal)`} strokeWidth='20' strokeLinecap='round' />

      <path d={CUP_BOWL} fill={`url(#${u}-face)`} stroke='#121317' strokeWidth='8' strokeLinejoin='miter' />

      <g clipPath={`url(#${u}-clip)`}>
        <path d='M150 184 L362 184 L362 212 L150 212 Z' fill='#000000' opacity='0.2' />
        <path d='M256 184 L300 184 L212 360 L168 360 Z' fill='#FFFFFF' opacity='0.09' />
        <path d='M150 184 L256 184 L256 360 L196 360 Z' fill='#000000' opacity='0.12' />
        <path d='M150 300 L362 300 L362 322 L150 322 Z' fill='#FFFFFF' opacity='0.06' />
      </g>

      <path d={CUP_BOWL} fill='none' stroke={t.m1} strokeWidth='2.5' opacity='0.55' />

      <rect x='142' y='156' width='228' height='30' rx='13' fill={`url(#${u}-metal)`} stroke='#121317' strokeWidth='8' />
      <rect x='162' y='164' width='188' height='7' rx='3.5' fill='#FFFFFF' opacity='0.3' />

      <path d={CUP_STEM} fill={`url(#${u}-metal2)`} stroke='#121317' strokeWidth='6' />
      <path d={CUP_BASE} fill={`url(#${u}-metal)`} stroke='#121317' strokeWidth='7' strokeLinejoin='miter' />
      <rect x='176' y='448' width='160' height='28' rx='9' fill={`url(#${u}-metal2)`} stroke='#121317' strokeWidth='6' />

      {RIVETS.map(([x, y], i) => (
        <g key={i}>
          <circle cx={x} cy={y} r='7' fill={`url(#${u}-metal)`} stroke='#121317' strokeWidth='3' />
          <circle cx={x - 2} cy={y - 2} r='2.4' fill='#FFFFFF' opacity='0.55' />
        </g>
      ))}

      <circle cx='256' cy='268' r='68' fill='#121317' opacity='0.9' />
      <circle cx='256' cy='268' r='62' fill={`url(#${u}-metal)`} stroke='#121317' strokeWidth='4' />
      <circle cx='256' cy='268' r='52' fill={`url(#${u}-core)`} stroke='#121317' strokeWidth='4' />

      <path d={GEM} fill={`url(#${u}-gemA)`} stroke='#121317' strokeWidth='3.5' strokeLinejoin='miter' />
      <path d='M256 228 L256 316 L210 292 L210 252 Z' fill={`url(#${u}-gemB)`} opacity='0.9' />
      <path d='M256 228 L302 252 L256 292 Z' fill='#FFFFFF' opacity='0.5' />
      <path d='M232 250 L256 228 L256 256 Z' fill='#FFFFFF' opacity='0.85' />

      <path d={CROWN} fill={`url(#${u}-metal)`} stroke='#121317' strokeWidth='7' strokeLinejoin='miter' />
      <rect x='186' y='132' width='140' height='28' rx='9' fill={`url(#${u}-metal2)`} stroke='#121317' strokeWidth='6' />
      <circle cx='210' cy='68' r='9' fill={t.g1} stroke='#121317' strokeWidth='4' />
      <circle cx='256' cy='44' r='10' fill={t.g1} stroke='#121317' strokeWidth='4' />
      <circle cx='302' cy='68' r='9' fill={t.g1} stroke='#121317' strokeWidth='4' />

      {xs.map((x, i) => (
        <path key={i} transform={`translate(${x} 490) scale(${sc})`} d={SPARK} fill={t.g1} stroke='#121317' strokeWidth='8' strokeLinejoin='miter' />
      ))}
    </svg>
  );
}
