import api from './client';
import type {
  Activity,
  ActivityCreateInput,
  ActivityParticipant,
  Page,
} from './types';

export interface MyActivitiesFilters extends ActivityFilters {
  /** Only upcoming/ongoing registrations; drops already-finished ones.
   *  Sends ?active_only=true. */
  active_only?: boolean;
}

export interface ActivityFilters {
  category?: string;
  /** Sport-category slug (racket/team/...). Sends ?sport_category=. */
  sport_category?: string;
  /** Activity-type slug, e.g. 'padel'. Sends ?type=<slug>. */
  type?: string;
  skill_level?: string;
  city?: string;
  venue_id?: string;
  search?: string;
  starts_after?: string;
  starts_before?: string;
  /** Only activities that have not started yet (sends ?upcoming=true). */
  upcoming?: boolean;
  limit?: number;
  offset?: number;
}

function clean<T extends object>(obj: T): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== ''),
  );
}

export async function listActivities(filters: ActivityFilters = {}): Promise<Page<Activity>> {
  const { data } = await api.get<Page<Activity>>('/api/v1/activities', {
    params: clean(filters),
  });
  return data;
}

export async function getActivity(id: string): Promise<Activity> {
  const { data } = await api.get<Activity>(`/api/v1/activities/${id}`);
  return data;
}

export async function createActivity(input: ActivityCreateInput): Promise<Activity> {
  const { data } = await api.post<Activity>('/api/v1/activities', input);
  return data;
}

export async function joinActivity(id: string): Promise<ActivityParticipant> {
  const { data } = await api.post<ActivityParticipant>(`/api/v1/activities/${id}/join`);
  return data;
}

export async function leaveActivity(id: string): Promise<void> {
  await api.post(`/api/v1/activities/${id}/leave`);
}

export async function listParticipants(id: string): Promise<ActivityParticipant[]> {
  const { data } = await api.get<ActivityParticipant[]>(`/api/v1/activities/${id}/participants`);
  return data;
}

export async function listMyActivities(
  filters: MyActivitiesFilters = {},
): Promise<Page<Activity>> {
  const { data } = await api.get<Page<Activity>>('/api/v1/activities/mine', {
    params: clean(filters),
  });
  return data;
}
