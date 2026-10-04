import api from './client';
import type { Club, ClubMember, Page } from './types';

export interface ClubFilters {
  category?: string;
  city?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export async function listClubs(filters: ClubFilters = {}): Promise<Page<Club>> {
  const { data } = await api.get<Page<Club>>('/api/v1/clubs', { params: filters });
  return data;
}

export async function getClub(id: string): Promise<Club> {
  const { data } = await api.get<Club>(`/api/v1/clubs/${id}`);
  return data;
}

export async function joinClub(id: string): Promise<ClubMember> {
  const { data } = await api.post<ClubMember>(`/api/v1/clubs/${id}/join`);
  return data;
}

export async function leaveClub(id: string): Promise<void> {
  await api.post(`/api/v1/clubs/${id}/leave`);
}

export async function listMembers(id: string): Promise<ClubMember[]> {
  const { data } = await api.get<ClubMember[]>(`/api/v1/clubs/${id}/members`);
  return data;
}
