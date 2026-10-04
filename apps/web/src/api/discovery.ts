import api from './client';
import type { MatchmakingResponse, UserProgress, VenueMapResponse } from './types';

function clean<T extends object>(obj: T): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== ''),
  );
}

/** Personalised activity + partner recommendations (auth required). */
export async function getMatchmaking(limit = 8): Promise<MatchmakingResponse> {
  const { data } = await api.get<MatchmakingResponse>('/api/v1/matchmaking/recommendations', {
    params: clean({ limit }),
  });
  return data;
}

/** Streak, active days and achievement progress for a user (public read). */
export async function getUserProgress(userId: string): Promise<UserProgress> {
  const { data } = await api.get<UserProgress>(`/api/v1/users/${userId}/streak`);
  return data;
}

export interface VenueMapFilters {
  limit?: number;
  category?: string;
  city?: string;
}

/** Every geocoded venue, for the interactive scatter map (public read). */
export async function getVenueMap(filters: VenueMapFilters = {}): Promise<VenueMapResponse> {
  const { data } = await api.get<VenueMapResponse>('/api/v1/venues/map', {
    params: clean({ limit: 300, ...filters }),
  });
  return data;
}
