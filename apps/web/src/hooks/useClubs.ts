import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as clubsApi from '@/api/clubs';
import { toast } from '@/store/toast';

const KEY = 'clubs';

export function useClubs(filters: clubsApi.ClubFilters = {}) {
  return useQuery({
    queryKey: [KEY, filters],
    queryFn: () => clubsApi.listClubs(filters),
    staleTime: 30_000,
  });
}

export function useClub(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'detail', id],
    queryFn: () => clubsApi.getClub(id as string),
    enabled: Boolean(id),
  });
}

export function useClubMembers(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'members', id],
    queryFn: () => clubsApi.listMembers(id as string),
    enabled: Boolean(id),
  });
}

export function useJoinClub(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => clubsApi.joinClub(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success('Bergabung ke komunitas');
    },
  });
}

export function useLeaveClub(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => clubsApi.leaveClub(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.info('Keluar dari komunitas');
    },
  });
}
