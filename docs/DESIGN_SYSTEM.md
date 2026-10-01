# DESIGN_SYSTEM.md — RALLY Design System

A premium, accessible, mobile-first design system. Dark and light themes are
first-class. Depth is **restrained** — CSS 3D / SVG, no gimmicks. Tokens are
driven by CSS variables and the brand single source of truth
(`apps/web/src/config/brand.ts`).

---

## 1. Principles

1. **Find your people, fast.** Discovery and joining are the hero actions.
2. **Calm, premium surfaces.** Generous spacing, low-noise chrome, real depth
   only where it communicates hierarchy.
3. **Accessible by default.** WCAG 2.2 AA where practical: contrast, focus,
   keyboard, labels, reduced motion.
4. **Mobile-first.** Design the phone, then enhance up to tablet, iPad, desktop.
5. **Consistency over novelty.** One component does one thing, everywhere.

---

## 2. Brand

- Name: **RALLY** (`BRAND_NAME`)
- Tagline: *Find your people. Do more together.* (`BRAND_TAGLINE`)
- Primary: `#6366f1` (indigo) · Accent: `#22d3ee` (cyan)
- Radius scale: base `0.75rem`
- Brand is swappable: change env vars, not components. Components read tokens,
  never hardcode hex values.

---

## 3. Color tokens (semantic)

Tokens are semantic, not literal. Themes remap the same names.

### Light theme
| token | value | use |
|-------|-------|-----|
| `--bg` | `#f8fafc` | app background |
| `--surface` | `#ffffff` | cards, sheets |
| `--surface-2` | `#f1f5f9` | raised / hover |
| `--border` | `#e2e8f0` | hairlines |
| `--text` | `#0f172a` | primary text |
| `--text-muted` | `#64748b` | secondary text |
| `--primary` | `#6366f1` | primary actions |
| `--accent` | `#0891b2` | highlights (darkened for contrast) |
| `--success` | `#16a34a` | confirmations |
| `--warning` | `#d97706` | cautions |
| `--danger` | `#dc2626` | destructive |

### Dark theme
| token | value | use |
|-------|-------|-----|
| `--bg` | `#0b1020` | app background |
| `--surface` | `#121a2e` | cards, sheets |
| `--surface-2` | `#1b2540` | raised / hover |
| `--border` | `#26314f` | hairlines |
| `--text` | `#e8edf7` | primary text |
| `--text-muted` | `#94a3b8` | secondary text |
| `--primary` | `#818cf8` | primary actions |
| `--accent` | `#22d3ee` | highlights |
| `--success` | `#4ade80` | confirmations |
| `--warning` | `#fbbf24` | cautions |
| `--danger` | `#f87171` | destructive |

Contrast targets: body text >= 4.5:1, large text >= 3:1, UI borders >= 3:1.
Theme switching sets `data-theme="dark|light"` on `<html>`; respects
`prefers-color-scheme` on first load, then user choice.

---

## 4. Typography

- Family: system UI stack (`ui-sans-serif, system-ui, -apple-system, Segoe UI,
  Roboto, Inter, sans-serif`); optional self-hosted Inter later.
- Scale (rem): `xs .75` · `sm .875` · `base 1` · `lg 1.125` · `xl 1.25` ·
  `2xl 1.5` · `3xl 1.875` · `4xl 2.25`.
- Weights: 400 body, 500 UI labels, 600 headings, 700 display.
- Line height: 1.5 body, 1.2 headings.
- Numeric data (MMR, scores, prices): `font-variant-numeric: tabular-nums`.

---

## 5. Spacing, radius, elevation

- Spacing scale (rem): `1 .25` · `2 .5` · `3 .75` · `4 1` · `6 1.5` · `8 2` ·
  `12 3` · `16 4`. 4px base grid.
- Radius: `sm .375` · `md .5` · `lg .75` · `xl 1` · `full 9999`. Cards use `lg`.
- Elevation (restrained depth):
  - `e0` flat (borders only)
  - `e1` `0 1px 2px rgba(0,0,0,.06)` — cards
  - `e2` `0 4px 12px rgba(0,0,0,.10)` — popovers, menus
  - `e3` `0 12px 32px rgba(0,0,0,.18)` — modals, sheets
- Depth uses shadow + subtle border, never heavy bevels. In dark theme, prefer
  border contrast over shadow.

---

## 6. Components (inventory)

Primitives (`components/ui/`):
- `Button` — variants: primary, secondary, ghost, danger; sizes sm/md/lg;
  loading + disabled states; icon support.
- `Input`, `Textarea`, `Select`, `Checkbox`, `Radio`, `Switch`, `DatePicker`.
- `Field` — label + hint + error wrapper; wires `aria-describedby`.
- `Card` — surface container with header/body/footer slots.
- `Badge`, `Tag`, `Chip` — status, category, skill band.
- `Avatar`, `AvatarGroup` — people, with fallback initials.
- `Tabs`, `Accordion`, `Dialog`/`Modal`, `Sheet` (mobile bottom sheet).
- `Toast` — transient feedback (aria-live polite).
- `Skeleton` — loading placeholders (no fake data, just shapes).
- `EmptyState` — icon + message + action.
- `Progress`, `Meter` — capacity, reputation, split progress.
- `Table` / `DataList` — responsive (cards on mobile).
- `Pagination`, `InfiniteScroll` sentinel.

Domain components (`components/`):
- `ActivityCard`, `ActivityFilters`, `CapacityMeter`.
- `VenueCard`, `AvailabilityGrid`, `BookingSummary`.
- `PaymentSplit`, `MoneyRow` (tabular nums).
- `ChatBubble`, `ConversationList`, `Composer`.
- `CheckInButton`, `ResultForm`, `VerificationList`.
- `MmrDelta` (+/- with arrow, color-safe: also sign + label).
- `LeaderboardTable`, `RankMedal`.
- `ReputationMeter`, `AchievementBadge`.
- `RoleBadge` — renders role; UI hint only (RBAC is server-side).

---

## 7. Layout & responsiveness

- Breakpoints: `sm 640` · `md 768` · `lg 1024` · `xl 1280` · `2xl 1536` (px).
- Targets: phone (<640), tablet (640–1023), iPad (768–1023, touch), desktop
  (>=1024).
- App shell: top bar (desktop) / bottom nav (mobile) + content region.
- Touch targets >= 44x44 px. Thumb-reachable primary actions on mobile.
- Grid: 4 col mobile, 8 col tablet, 12 col desktop.
- Container max width `1280px`, generous gutters.

---

## 8. Motion

- Durations: `fast 120ms` · `base 200ms` · `slow 320ms`.
- Easing: `standard cubic-bezier(.2,.8,.2,1)`; `enter` slight overshoot;
  `exit` ease-in.
- Respect `prefers-reduced-motion: reduce` -> disable non-essential motion.
- Restrained 3D: card tilt/hover lift, flip for leaderboard rank change, SVG
  line-draw for MMR charts. No gratuitous parallax.

---

## 9. Accessibility (WCAG 2.2 AA where practical)

- Semantic HTML first; ARIA only to fill gaps.
- All interactive elements keyboard reachable; visible focus ring
  (`--primary`, 2px offset).
- Form fields always labelled; errors announced and tied via `aria-describedby`.
- Color is never the only signal (MMR delta shows sign + text, not just color).
- Live regions for toasts and chat (`aria-live`).
- Respect reduced motion; avoid motion-triggered content.
- Minimum contrast enforced via tokens; audit with axe in CI later.
- Focus management for modals/sheets (trap + restore).

---

## 10. Iconography & imagery

- Icons: single line-icon set (stroke-based), consistent 24px grid, 1.5px
  stroke. Activity category icons distinct per category.
- Imagery: original or licensed; never third-party proprietary assets.
- Avatars: initials fallback; no default stock faces presented as real people.

---

## 11. Content & tone

- Voice: friendly, direct, encouraging. Short sentences.
- Buttons: verb-first ("Join activity", "Split cost", "Verify result").
- Empty states guide the next action.
- Money and stats use tabular numerals and explicit currency.
- Dev/mock providers surface a clear label ("Test payments — no real charge").

---

## 12. Implementation notes

- Tokens exposed as CSS variables in `styles/tokens.css`; Tailwind config maps
  semantic names to these variables.
- `brand.ts` drives theme values (primary/accent/radius) into CSS variables at
  runtime, so rebranding needs no component edits.
- Component API: typed props, `className` passthrough, `data-*` for state.
- Storybook-style local gallery planned under `apps/web/src/components/ui`.
- No fake data in components; loading -> `Skeleton`, empty -> `EmptyState`.
