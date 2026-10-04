import { useQuery } from '@tanstack/react-query';
import * as discoveryApi from '@/api/discovery';
import { useAuthStore } from '@/store/auth';

const KEY = 'discovery';

/** Activity + partner recommendations for the signed-in user. */
export function useMatchmaking(limit = 8) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: [KEY, 'matchmaking', limit],
    queryFn: () => discoveryApi.getMatchmaking(limit),
    enabled: Boolean(token),
    staleTime: 30_000,
  });
}

/** Streak, active days and achievements for a user (public read). */
export function useUserProgress(userId: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'progress', userId],
    queryFn: () => discoveryApi.getUserProgress(userId as string),
    enabled: Boolean(userId),
    staleTime: 30_000,
  });
}

/** Geocoded venues for the interactive map (public read). */
export function useVenueMap(filters: discoveryApi.VenueMapFilters = {}) {
  return useQuery({
    queryKey: [KEY, 'venue-map', filters],
    queryFn: () => discoveryApi.getVenueMap(filters),
    staleTime: 60_000,
  });
}
