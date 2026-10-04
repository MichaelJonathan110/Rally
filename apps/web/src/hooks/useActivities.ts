import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as activitiesApi from '@/api/activities';
import type { Activity, ActivityCreateInput } from '@/api/types';
import { useAuthStore } from '@/store/auth';
import { toast } from '@/store/toast';

const KEY = 'activities';

export function useActivities(filters: activitiesApi.ActivityFilters = {}) {
  return useQuery({
    queryKey: [KEY, filters],
    queryFn: () => activitiesApi.listActivities(filters),
    staleTime: 15_000,
  });
}

/** Activities the signed-in user has joined or is hosting. */
export function useMyActivities(filters: activitiesApi.MyActivitiesFilters = {}) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: [KEY, 'mine', filters],
    queryFn: () => activitiesApi.listMyActivities(filters),
    enabled: Boolean(token),
    staleTime: 10_000,
  });
}

export function useActivity(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'detail', id],
    queryFn: () => activitiesApi.getActivity(id as string),
    enabled: Boolean(id),
  });
}

export function useActivityParticipants(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'participants', id],
    queryFn: () => activitiesApi.listParticipants(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateActivity() {
  const qc = useQueryClient();
  return useMutation<Activity, unknown, ActivityCreateInput>({
    mutationFn: activitiesApi.createActivity,
    onSuccess: (a) => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success('Kegiatan dibuat', a.title);
    },
  });
}

export function useJoinActivity(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => activitiesApi.joinActivity(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success('Berhasil ikut', 'Sampai jumpa di lapangan!');
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error('Gagal ikut kegiatan', detail ?? 'Coba lagi sebentar lagi.');
    },
  });
}

export function useLeaveActivity(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => activitiesApi.leaveActivity(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.info('Keluar dari kegiatan');
    },
  });
}
