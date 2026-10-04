# RALLY — DESIGN SYSTEM

Token-level specification for the RALLY light/pastel visual language.
Source of truth for the skill `rally-design`. Implemented in
`apps/web/tailwind.config.js` and `apps/web/src/index.css`.

## 1. Principles
- **Paper, not glass.** Warm off-white/beige base, white surfaces, soft shadows.
- **Type is the hero.** Big bold near-black headlines; type creates moments.
- **Pastel identity + minimal data viz.** Pastels = identity/data. One deep-coral action accent.
- **People break the frame.** Human cutouts overlap the UI.
- **3D = interface, not decoration.** Every visual object maps to a real function, with a
  conventional UI equivalent always present.
- **Anti-AI-slop.** No identical card grids, no random blobs, no KPI walls, no glass everywhere.

## 2. Colour tokens
### Base / surface
| token | hex | use |
|---|---|---|
| `bg` (paper) | `#FAF6F0` | page background (warm off-white) |
| `bg-warm` | `#F2ECE2` | warm beige band / alt section |
| `surface` | `#FFFFFF` | cards, sheets |
| `surface-muted` | `#FBF8F3` | inset panels |
| `line` | `#E8E0D4` | hairlines / borders |
| `line-strong` | `#D9CFBE` | emphasised dividers |

### Ink / text
| token | hex | use |
|---|---|---|
| `ink` | `#141414` | big bold type, headings |
| `ink-2` | `#5C5C5C` | body / secondary text |
| `ink-3` | `#8A8A8A` | meta / captions |
| `ink-inv` | `#FFFFFF` | text on coral/dark fills |

### Pastel identity (category + data viz)
| token | hex |
|---|---|
| `cyan` | `#9FE3DC` |
| `mint` | `#B9E9C9` |
| `lime` | `#D9F08C` |
| `yellow` | `#FFE28A` |
| `coral` | `#FF9C86` |

### Semantic
| token | hex | use |
|---|---|---|
| `action` (deep coral) | `#FF6F55` | THE one "do this" colour: CTA, active, MMR progress |
| `action-ink` | `#FFFFFF` | text on action |
| `success` | `#4FBF8B` | confirmed / joined |
| `warning` | `#F2C14E` | almost-full / pending |
| `danger` | `#F07C6C` | error / cancel |

**Rule:** pastels carry identity + data; deep coral is the single action accent, used with
restraint.

### Category -> pastel map
padel/badminton/tennis → cyan · billiard/board-games → mint · futsal/football/hiking → lime ·
gym/volleyball → yellow · basketball/social/party → coral · music/creative → coral.
Full mapping lives in `apps/web/src/config/categories.ts`.

## 3. Typography
Fonts: **Sora** (display, 700/800/900) + **Plus Jakarta Sans** (sans, 400-800).
| token | size / line / tracking | use |
|---|---|---|
| `display` | clamp(2.75rem, 7vw, 5.5rem) / 0.94 / -0.035em | hero anchors |
| `display-sm` | clamp(2rem, 4.5vw, 3.25rem) / 1.0 / -0.025em | section heroes |
| `h1` | 1.75rem / 1.15 / -0.02em | page titles |
| `h2` | 1.375rem / 1.2 / -0.015em | section titles |
| `h3` | 1.0625rem / 1.3 | card titles |
| `body` | 0.9375rem / 1.55 | paragraphs |
| `meta` | 0.75rem / 1.4 / 0.02em | metadata |
| `eyebrow` | 0.6875rem / 1.2 / 0.18em UPPERCASE | small labels |

## 4. Spacing (8pt rhythm)
`0.25 0.5 0.75 1 1.5 2 3 4 6 8 12 16 24` → 4,8,12,16,24,32,48,64,96,128,192,384px.
Section vertical padding: mobile `48px`, desktop `96px`. Gutter: `16 / 24 / 32`.

## 5. Radius
`sm 10px` · `md 14px` · `lg 20px` · `xl 28px` · `2xl 36px` · `pill 999px`.
Large radii are allowed but must be broken up by cutouts, splits and rails — not applied to
a uniform card grid.

## 6. Shadow (soft, warm-tinted; never harsh)
| token | value |
|---|---|
| `soft` | `0 1px 2px rgba(20,20,20,.04), 0 10px 30px -18px rgba(20,20,20,.18)` |
| `lift` | `0 24px 60px -28px rgba(20,20,20,.28)` |
| `pop` | `0 12px 40px -16px rgba(255,111,85,.35)` (action elements) |
| `ring` | `0 0 0 1px rgba(20,20,20,.06)` |

## 7. Borders
Default hairline `1px solid #E8E0D4`. Prefer fewer borders + whitespace over boxed sections.

## 8. Motion
| token | duration | ease |
|---|---|---|
| `fast` | 120ms | `cubic-bezier(.2,.8,.2,1)` |
| `base` | 220ms | `cubic-bezier(.2,.8,.2,1)` |
| `slow` | 380ms | `cubic-bezier(.16,1,.3,1)` |
| `spring` | 420ms | `cubic-bezier(.16,1,.3,1)` |
Reduced motion: durations -> ~0ms, `scroll-behavior:auto`.

## 9. Z-index scale
`base 0` · `raised 10` · `sticky 30` · `overlay 40` · `drawer 50` · `modal 60` · `toast 70`.

## 10. Breakpoints
`xs 360` · `sm 640` · `md 768` · `lg 1024` · `xl 1280` · `2xl 1536` · `3xl 1920`.
Design mobile-first; desktop gets editorial (asymmetric) compositions, not a stretched phone.

## 11. 3D / depth tiers
| tier | depth | when |
|---|---|---|
| `flat` | 0 | static SVG / fallback |
| `raised` | shadow `soft` | default surfaces |
| `floating` | shadow `lift` + translateY(-2px) | interactive hover |
| `immersive` | layered + parallax | hero objects (lazy, reduced-motion aware) |
Performance tiers: HIGH / MEDIUM / LOW / STATIC (see brief §25). Every 3D interaction has a
conventional UI equivalent.

## 12. Component inventory
Reusable components (brief §27): `Logo`, `Button`, `Badge`, `Card`, `SectionHeader`,
`ActivityCard`, `ActivityHero`, `CategoryRail`, `StatTile`, `MMRCard`, `RankBadge`,
`PlayerCard`, `VenueCard`, `BookingSlot`, `Leaderboard`, `Cutout`, `EmptyState`,
`ErrorState`, `Skeleton`. Build once, reuse everywhere.

## 13. Usage rules (do / don't)
- DO lead every page with a type anchor or a human image moment.
- DO keep the action colour rare — one primary CTA per view.
- DON'T box every section; use whitespace and hairlines.
- DON'T ship a 3-card grid as the whole page; break it with a rail/split/feature.
- DON'T hardcode hex values in components — use the tokens above.
