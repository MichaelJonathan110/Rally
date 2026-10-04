/**
 * Catalog endpoints: the city list and the activity-type registry.
 *
 * These power the city onboarding + the "jenis kegiatan" filter without
 * changing the activity response shape. See the verified API contract.
 */
import api from './client';

export interface CityCount {
  city: string;
  count: number;
}

export interface ActivityType {
  slug: string;
  label_id: string;
  label_en: string;
  category: string;
}

export async function listCities(): Promise<CityCount[]> {
  const { data } = await api.get<CityCount[]>('/api/v1/cities');
  return data;
}

export async function listActivityTypes(): Promise<ActivityType[]> {
  const { data } = await api.get<ActivityType[]>('/api/v1/activity-types');
  return data;
}
