import { useQuery } from '@tanstack/react-query';
import * as lbApi from '@/api/leaderboard';
import * as notifApi from '@/api/notifications';
import { useAuthStore } from '@/store/auth';

export function useLeaderboard(activityId: string | undefined, period = 'all_time') {
  return useQuery({
    queryKey: ['leaderboard', activityId, period],
    queryFn: () => lbApi.getLeaderboard(activityId as string, period),
    enabled: Boolean(activityId),
  });
}


export function useNotifications(unreadOnly = false) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ['notifications', unreadOnly],
    queryFn: () => notifApi.listNotifications(unreadOnly),
    staleTime: 20_000,
    // Guests are not authenticated: never call a protected endpoint, which
    // would 401 and (previously) bounce the public pages to /login.
    enabled: Boolean(token),
  });
}
