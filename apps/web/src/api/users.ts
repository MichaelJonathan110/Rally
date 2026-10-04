import api from './client';
import type { User, UserRatings } from './types';

export interface Achievement {
  id: string;
  code: string;
  name: string;
  description: string | null;
  icon: string | null;
  points: number;
}

export interface UserAchievement {
  achievement: Achievement;
  earned_at: string | null;
}

/** Fields the signed-in user may change on their own profile (PATCH /users/me). */
export interface UserUpdateInput {
  display_name?: string;
  bio?: string;
  avatar_url?: string | null;
  city?: string;
  skill_level?: string;
}

/** Per-category MMR ratings + immutable history for a user (public read). */
export async function getUserRatings(userId: string): Promise<UserRatings> {
  const { data } = await api.get<UserRatings>(`/api/v1/users/${userId}/ratings`);
  return data;
}

export async function getUserAchievements(userId: string): Promise<UserAchievement[]> {
  const { data } = await api.get<UserAchievement[]>(`/api/v1/users/${userId}/achievements`);
  return data;
}

/** Update the caller's own profile; returns the refreshed user record. */
export async function updateMe(input: UserUpdateInput): Promise<User> {
  const { data } = await api.patch<User>('/api/v1/users/me', input);
  return data;
}
