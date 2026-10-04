import api from './client';
import type { Page, Venue, VenueCourt } from './types';

export interface VenueFilters {
  city?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export async function listVenues(filters: VenueFilters = {}): Promise<Page<Venue>> {
  const { data } = await api.get<Page<Venue>>('/api/v1/venues', { params: filters });
  return data;
}

export async function getVenue(id: string): Promise<Venue> {
  const { data } = await api.get<Venue>(`/api/v1/venues/${id}`);
  return data;
}

export async function listCourts(id: string): Promise<VenueCourt[]> {
  const { data } = await api.get<VenueCourt[]>(`/api/v1/venues/${id}/courts`);
  return data;
}
