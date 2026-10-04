import api from './client';
import type { Health } from './types';

export async function getHealth(): Promise<Health> {
  const { data } = await api.get<Health>('/health');
  return data;
}
