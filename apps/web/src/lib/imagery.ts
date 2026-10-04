/**
 * Centralised imagery module.
 *
 * Every photo is a stable Unsplash CDN URL. Each category carries a light
 * pastel gradient fallback so the UI still looks composed when the network is
 * unavailable - no broken-image boxes, ever. Photos are of real people in
 * motion, cropped and masked so they fuse with the interface (see
 * `components/visuals/ActivityVisual`).
 */
import type { ActivityCategory } from '@/api/types';
import { categoryMeta, TONE, type Tone } from '@/config/categories';

const CDN = 'https://images.unsplash.com';

export function unsplash(id: string, w = 1200): string {
  return `${CDN}/${id}?auto=format&fit=crop&w=${w}&q=70`;
}

/** Hero photograph - a runner in motion, the signature image of the brand. */
export const HERO_IMAGE = unsplash('photo-1552674605-db6ffd4facb5', 1600);

export interface CategoryImage {
  /** Primary hero/cover photo for the category. */
  cover: string;
  /** A few additional photos for cards/rails. */
  gallery: string[];
  /** CSS gradient used as a graceful fallback behind transparent photos. */
  gradient: string;
}

function toneGradient(tone: Tone): string {
  return TONE[tone].gradient;
}

/** Category -> imagery + pastel gradient fallback. */
export const CATEGORY_IMAGERY: Record<ActivityCategory, CategoryImage> = {
  racket: {
    cover: unsplash('photo-1626224583764-f87db24ac4ea'),
    gallery: [
      unsplash('photo-1657704358775-ed705c7388d2'),
      unsplash('photo-1545151414-8a948e1ea54f'),
      unsplash('photo-1708312604109-16c0be9326cd'),
    ],
    gradient: toneGradient('cyan'),
  },
  team: {
    cover: unsplash('photo-1577416412292-747c6607f055'),
    gallery: [
      unsplash('photo-1606925797300-0b35e9d1794e'),
      unsplash('photo-1554068865-24cecd4e34b8'),
      unsplash('photo-1517649763962-0c623066013b'),
    ],
    gradient: toneGradient('lime'),
  },
  combat: {
    cover: unsplash('photo-1613918431703-aa50889e3be9'),
    gallery: [
      unsplash('photo-1599058917765-a780eda07a3e'),
      unsplash('photo-1517836357463-d25dfeac3438'),
      unsplash('photo-1571902943202-507ec2618e8f'),
    ],
    gradient: toneGradient('coral'),
  },
  strength: {
    cover: unsplash('photo-1534438327276-14e5300c3a48'),
    gallery: [
      unsplash('photo-1576678927484-cc907957088c'),
      unsplash('photo-1517836357463-d25dfeac3438'),
      unsplash('photo-1599058917765-a780eda07a3e'),
    ],
    gradient: toneGradient('yellow'),
  },
  running: {
    cover: unsplash('photo-1552674605-db6ffd4facb5'),
    gallery: [
      unsplash('photo-1744060204728-f68e434a3edf'),
      unsplash('photo-1571019613454-1cb2f99b2d8b'),
    ],
    gradient: toneGradient('mint'),
  },
  cycling: {
    cover: unsplash('photo-1541625602330-2277a4c46182'),
    gallery: [
      unsplash('photo-1534146789009-76ed5060ec70'),
      unsplash('photo-1470071459604-3b5ec3a7fe05'),
    ],
    gradient: toneGradient('neutral'),
  },
  water: {
    cover: unsplash('photo-1669185694564-2da287319e13'),
    gallery: [
      unsplash('photo-1533105079780-92b9be482077'),
      unsplash('photo-1506905925346-21bda4d32df4'),
    ],
    gradient: toneGradient('cyan'),
  },
  winter: {
    cover: unsplash('photo-1506905925346-21bda4d32df4'),
    gallery: [
      unsplash('photo-1470071459604-3b5ec3a7fe05'),
      unsplash('photo-1441974231531-c6227db76b6e'),
    ],
    gradient: toneGradient('mint'),
  },
  precision: {
    cover: unsplash('photo-1610890716171-6b1bb98ffd09'),
    gallery: [
      unsplash('photo-1575553939928-d03b21323afe'),
      unsplash('photo-1606167668584-78701c57f13d'),
      unsplash('photo-1677188010559-0667a1ed33a0'),
    ],
    gradient: toneGradient('yellow'),
  },
  gymnastics: {
    cover: unsplash('photo-1599901860904-17e6ed7083a0'),
    gallery: [
      unsplash('photo-1517836357463-d25dfeac3438'),
      unsplash('photo-1460661419201-fd4cecdf8a8b'),
    ],
    gradient: toneGradient('coral'),
  },
  outdoor: {
    cover: unsplash('photo-1551632811-561732d1e306'),
    gallery: [
      unsplash('photo-1757481102369-1c01de59da69'),
      unsplash('photo-1562593028-1fe2d15bde36'),
      unsplash('photo-1470246973918-29a93221c455'),
      unsplash('photo-1441974231531-c6227db76b6e'),
    ],
    gradient: toneGradient('lime'),
  },
  other: {
    cover: unsplash('photo-1524758631624-e2822e304c36'),
    gallery: [unsplash('photo-1497366754035-f200968a6e72')],
    gradient: toneGradient('neutral'),
  },
};


/** Activity-type -> fixed, relevant photo. Every activity of a given type
 *  shows the SAME image, so a Padel card always looks like padel, a Futsal
 *  card like futsal, and so on. Falls back to the category pool when the
 *  type is unknown. */
export const ACTIVITY_TYPE_IMAGE: Record<string, string> = {
  // Racket
  badminton: unsplash('photo-1708312604109-16c0be9326cd'),
  padel: unsplash('photo-1657704358775-ed705c7388d2'),
  tennis: unsplash('photo-1545151414-8a948e1ea54f'),
  // Team
  football: unsplash('photo-1517649763962-0c623066013b'),
  futsal: unsplash('photo-1606925797300-0b35e9d1794e'),
  basketball: unsplash('photo-1577416412292-747c6607f055'),
  'basketball-3x3': unsplash('photo-1577416412292-747c6607f055'),
  volleyball: unsplash('photo-1554068865-24cecd4e34b8'),
  'beach-volleyball': unsplash('photo-1554068865-24cecd4e34b8'),
  handball: unsplash('photo-1554068865-24cecd4e34b8'),
  rugby: unsplash('photo-1517649763962-0c623066013b'),
  'rugby-sevens': unsplash('photo-1517649763962-0c623066013b'),
  'american-football': unsplash('photo-1517649763962-0c623066013b'),
  // Combat
  boxing: unsplash('photo-1613918431703-aa50889e3be9'),
  kickboxing: unsplash('photo-1613918431703-aa50889e3be9'),
  'muay-thai': unsplash('photo-1613918431703-aa50889e3be9'),
  mma: unsplash('photo-1599058917765-a780eda07a3e'),
  bjj: unsplash('photo-1599058917765-a780eda07a3e'),
  judo: unsplash('photo-1599058917765-a780eda07a3e'),
  karate: unsplash('photo-1571902943202-507ec2618e8f'),
  taekwondo: unsplash('photo-1571902943202-507ec2618e8f'),
  wrestling: unsplash('photo-1599058917765-a780eda07a3e'),
  // Strength
  weightlifting: unsplash('photo-1576678927484-cc907957088c'),
  powerlifting: unsplash('photo-1576678927484-cc907957088c'),
  bodybuilding: unsplash('photo-1534438327276-14e5300c3a48'),
  crossfit: unsplash('photo-1534438327276-14e5300c3a48'),
  strongman: unsplash('photo-1534438327276-14e5300c3a48'),
  calisthenics: unsplash('photo-1517836357463-d25dfeac3438'),
  // Running / athletics
  running: unsplash('photo-1744060204728-f68e434a3edf'),
  sprinting: unsplash('photo-1744060204728-f68e434a3edf'),
  marathon: unsplash('photo-1744060204728-f68e434a3edf'),
  'half-marathon': unsplash('photo-1744060204728-f68e434a3edf'),
  'trail-running': unsplash('photo-1551632811-561732d1e306'),
  'track-field': unsplash('photo-1571019613454-1cb2f99b2d8b'),
  'long-jump': unsplash('photo-1571019613454-1cb2f99b2d8b'),
  'high-jump': unsplash('photo-1571019613454-1cb2f99b2d8b'),
  'pole-vault': unsplash('photo-1571019613454-1cb2f99b2d8b'),
  'shot-put': unsplash('photo-1571019613454-1cb2f99b2d8b'),
  discus: unsplash('photo-1571019613454-1cb2f99b2d8b'),
  javelin: unsplash('photo-1571019613454-1cb2f99b2d8b'),
  // Cycling
  'road-cycling': unsplash('photo-1541625602330-2277a4c46182'),
  'mountain-biking': unsplash('photo-1534146789009-76ed5060ec70'),
  bmx: unsplash('photo-1534146789009-76ed5060ec70'),
  'track-cycling': unsplash('photo-1534146789009-76ed5060ec70'),
  'gravel-cycling': unsplash('photo-1541625602330-2277a4c46182'),
  // Water
  swimming: unsplash('photo-1669185694564-2da287319e13'),
  diving: unsplash('photo-1669185694564-2da287319e13'),
  'open-water-swimming': unsplash('photo-1533105079780-92b9be482077'),
  surfing: unsplash('photo-1506905925346-21bda4d32df4'),
  windsurfing: unsplash('photo-1506905925346-21bda4d32df4'),
  sailing: unsplash('photo-1506905925346-21bda4d32df4'),
  kayaking: unsplash('photo-1533105079780-92b9be482077'),
  canoeing: unsplash('photo-1533105079780-92b9be482077'),
  rowing: unsplash('photo-1533105079780-92b9be482077'),
  rafting: unsplash('photo-1533105079780-92b9be482077'),
  'water-polo': unsplash('photo-1669185694564-2da287319e13'),
  // Winter
  'ice-hockey': unsplash('photo-1506905925346-21bda4d32df4'),
  'figure-skating': unsplash('photo-1470071459604-3b5ec3a7fe05'),
  'speed-skating': unsplash('photo-1470071459604-3b5ec3a7fe05'),
  'short-track': unsplash('photo-1470071459604-3b5ec3a7fe05'),
  curling: unsplash('photo-1441974231531-c6227db76b6e'),
  skiing: unsplash('photo-1551698618-1dfe5d97d256'),
  snowboarding: unsplash('photo-1551698618-1dfe5d97d256'),
  // Precision
  golf: unsplash('photo-1610890716171-6b1bb98ffd09'),
  bowling: unsplash('photo-1606167668584-78701c57f13d'),
  billiards: unsplash('photo-1575553939928-d03b21323afe'),
  pool: unsplash('photo-1575553939928-d03b21323afe'),
  snooker: unsplash('photo-1575553939928-d03b21323afe'),
  darts: unsplash('photo-1606167668584-78701c57f13d'),
  archery: unsplash('photo-1610890716171-6b1bb98ffd09'),
  shooting: unsplash('photo-1610890716171-6b1bb98ffd09'),
  chess: unsplash('photo-1524758631624-e2822e304c36'),
  // Gymnastics
  'artistic-gymnastics': unsplash('photo-1599901860904-17e6ed7083a0'),
  'rhythmic-gymnastics': unsplash('photo-1599901860904-17e6ed7083a0'),
  trampoline: unsplash('photo-1460661419201-fd4cecdf8a8b'),
  // Outdoor / climbing
  'sport-climbing': unsplash('photo-1757481102369-1c01de59da69'),
  bouldering: unsplash('photo-1757481102369-1c01de59da69'),
  'rock-climbing': unsplash('photo-1757481102369-1c01de59da69'),
  mountaineering: unsplash('photo-1562593028-1fe2d15bde36'),
  hiking: unsplash('photo-1562593028-1fe2d15bde36'),
  trekking: unsplash('photo-1562593028-1fe2d15bde36'),
  // Other sports
  'sepak-takraw': unsplash('photo-1517649763962-0c623066013b'),
  equestrian: unsplash('photo-1553284965-83fd3e82fa5a'),
  skateboarding: unsplash('photo-1547447134-cd3f5c716030'),
  'roller-skating': unsplash('photo-1547447134-cd3f5c716030'),
};

/** Deterministic hash -> stable index so a given activity always gets one photo. */
function hash(value: string): number {
  let h = 0;
  for (let i = 0; i < value.length; i += 1) {
    h = (h << 5) - h + value.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export function categoryCover(category: string | null | undefined, w = 1200): string {
  const entry = CATEGORY_IMAGERY[categoryMeta(category).id] ?? CATEGORY_IMAGERY.other;
  return w === 1200 ? entry.cover : entry.cover.replace('w=1200', `w=${w}`);
}

export function categoryGradient(category: string | null | undefined): string {
  return (CATEGORY_IMAGERY[categoryMeta(category).id] ?? CATEGORY_IMAGERY.other).gradient;
}

/** Stable per-activity photo (varies within a category, never random on re-render). */
export function activityImage(
  activity: { id: string; category: string | null | undefined; activity_type?: string | null },
  w = 1200,
): string {
  const fixed = activity.activity_type ? ACTIVITY_TYPE_IMAGE[activity.activity_type] : undefined;
  if (fixed) {
    return w === 1200 ? fixed : fixed.replace('w=1200', `w=${w}`);
  }
  const entry = CATEGORY_IMAGERY[categoryMeta(activity.category).id] ?? CATEGORY_IMAGERY.other;
  const pool = [entry.cover, ...entry.gallery];
  const picked = pool[hash(activity.id) % pool.length];
  return picked.replace('w=1200', `w=${w}`);
}

export function activityGradient(activity: { category: string | null | undefined }): string {
  return categoryGradient(activity.category);
}
