# RALLY — DESIGN DIRECTION

_Authored from the user's own art-direction brief (`rally-design` skill ->
`references/visual-direction-light.md`) and the three visual references.
This document is the human-readable "why"; `DESIGN_SYSTEM.md` is the token-level "what"._

## One-line direction
**Light, soft, premium editorial fitness/social.** Off-white and warm-beige paper, pastel
data colours, **big bold black type**, human cutout photography fused with the UI,
generous whitespace, mobile-first. RALLY is a **WORLD OF ACTIVITIES** - not a dashboard.

## The five signals that make it RALLY (and not AI-slop)
1. **Paper, not glass.** Backgrounds are warm off-white (#FAF6F0) and beige (#F2ECE2),
   surfaces are pure white (#FFFFFF) with *very soft* shadows. No dark UI, no neon, no
   heavy glassmorphism.
2. **Type is the hero.** Oversized, tight-tracking, near-black (#141414) headlines
   (Sora/Archivo, 800-900). Type creates *moments*; it is not repeated everywhere.
3. **Pastel identity.** cyan/mint/lime/yellow/coral carry category identity and data
   viz on white, thin strokes, minimal chart junk. A single **deep coral #FF6F55** is the
   one "do this" colour (active state, MMR progress, selected activity).
4. **People break the frame.** Real human photography / cutouts overlap cards and cross
   under big black type - the signature move of the references.
5. **Asymmetry and whitespace.** Editorial splits, offset blocks, horizontal rails - never
   a `[Card][Card][Card]` grid, never 12 identical tiles, never everything boxed.

## Reference -> principle translation (observe, imitate, modify - never copy)
- REF1 (agency mobile UI): confident hierarchy, editorial mobile screens.
- REF2 (fitness app, "image of a person running"): big hero image of a person in motion,
  fresh and modern - becomes our hero cutout.
- REF3 (direct JPG): light composition with soft colour accents and large type.
- Common principles: **light paper base, one dominant human subject, bold type anchor,
  restrained pastel accent, lots of air.**

## Anti-patterns we explicitly avoid
Dark UI - neon/cyberpunk - heavy glass - endless identical rounded cards - rainbow
gradients/random blobs - KPI tile grids - giant meaningless headings - generic stock-photo
grids - decorative 3D with no function.

## 3D = interface, not decoration
Any 3D/visual object maps to a real function and ALWAYS has a conventional UI equivalent
(button / list / select). Visual experimentation must never cost booking reliability,
search, navigation, chat, payments, MMR, leaderboards or event management.

## Indonesia localisation
Cities (Jakarta, Bandung, Surabaya, Yogyakarta, Denpasar/Bali, Medan, Makassar, Semarang),
**real** venues and named activities, currency **IDR** (`Rp 75.000`) or `Gratis` when free,
UI copy in Bahasa Indonesia. Real place names only.

## Motion
Intentional only: fast 100-150ms, normal 180-300ms, emphasis 300-500ms; spring easing;
respect `prefers-reduced-motion` (all animation collapses to ~0ms).
