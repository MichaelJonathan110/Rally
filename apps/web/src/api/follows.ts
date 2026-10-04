import api from './client';
import type { FollowCounts, FollowList } from './types';

export async function followUser(id: string): Promise<void> {
  await api.post(`/api/v1/users/${id}/follow`);
}

export async function unfollowUser(id: string): Promise<void> {
  await api.delete(`/api/v1/users/${id}/follow`);
}

export async function getFollowSuggestions(limit = 8): Promise<FollowList> {
  const { data } = await api.get<FollowList>('/api/v1/me/follow-suggestions', {
    params: { limit },
  });
  return data;
}

export async function getMyFollowing(): Promise<FollowList> {
  const { data } = await api.get<FollowList>('/api/v1/me/following');
  return data;
}

export async function getMyFriends(): Promise<FollowList> {
  const { data } = await api.get<FollowList>('/api/v1/me/friends');
  return data;
}

export async function getFollowCounts(id: string): Promise<FollowCounts> {
  const { data } = await api.get<FollowCounts>(`/api/v1/users/${id}/follow-counts`);
  return data;
}
