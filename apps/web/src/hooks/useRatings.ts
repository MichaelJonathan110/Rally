import { useQuery } from '@tanstack/react-query';
import * as usersApi from '@/api/users';

/** Per-category MMR ratings + history for a user. */
export function useUserRatings(userId: string | undefined) {
  return useQuery({
    queryKey: ['ratings', userId],
    queryFn: () => usersApi.getUserRatings(userId as string),
    enabled: Boolean(userId),
    staleTime: 30_000,
  });
}

export function useUserAchievements(userId: string | undefined) {
  return useQuery({
    queryKey: ['achievements', userId],
    queryFn: () => usersApi.getUserAchievements(userId as string),
    enabled: Boolean(userId),
    staleTime: 60_000,
  });
}
