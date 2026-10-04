import api from './client';
import type { LeaderboardEntry, UserRatings } from './types';

export async function getLeaderboard(
  activityId: string,
  period = 'all_time',
): Promise<LeaderboardEntry[]> {
  const { data } = await api.get<LeaderboardEntry[]>(
    `/api/v1/activities/${activityId}/leaderboard`,
    { params: { period } },
  );
  return data;
}

export async function getUserRatings(userId: string): Promise<UserRatings> {
  const { data } = await api.get<UserRatings>(`/api/v1/users/${userId}/ratings`);
  return data;
}
