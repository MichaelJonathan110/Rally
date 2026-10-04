/**
 * Chosen-city store (Phase 2 onboarding).
 *
 * The user's city is remembered in localStorage under `rally.city` so the home
 * page and /discover default to it. Three states:
 *   - `undefined`  -> not chosen yet (show the onboarding picker)
 *   - ''           -> explicitly "all cities"
 *   - 'Jakarta'    -> a specific city
 *
 * The store is deliberately tiny and synchronous so the header selector and the
 * hero onboarding stay in sync everywhere.
 */
import { create } from 'zustand';

const CITY_KEY = 'rally.city';

/** Sentinel stored for "all cities" so it is distinct from "not chosen". */
export const ALL_CITIES = '';

function readCity(): string | undefined {
  try {
    if (typeof localStorage === 'undefined') return undefined;
    const v = localStorage.getItem(CITY_KEY);
    return v === null ? undefined : v;
  } catch {
    return undefined;
  }
}

interface CityState {
  /** `undefined` = not chosen, `''` = all cities, otherwise the city name. */
  city: string | undefined;
  hasChosen: boolean;
  setCity: (city: string) => void;
  clearCity: () => void;
}

export const useCityStore = create<CityState>((set) => ({
  city: readCity(),
  hasChosen: readCity() !== undefined,
  setCity: (city) => {
    try {
      localStorage.setItem(CITY_KEY, city);
    } catch {
      /* storage unavailable - choice still applies for this session */
    }
    set({ city, hasChosen: true });
  },
  clearCity: () => {
    try {
      localStorage.removeItem(CITY_KEY);
    } catch {
      /* ignore */
    }
    set({ city: undefined, hasChosen: false });
  },
}));

/** Non-reactive read for handlers / query builders. */
export function getCity(): string | undefined {
  return useCityStore.getState().city;
}

/** The value to send to the API: a city name, or undefined for "all cities". */
export function cityParam(city: string | undefined): string | undefined {
  return city ? city : undefined;
}
