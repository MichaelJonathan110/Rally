import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as followsApi from '@/api/follows';
import { useAuthStore } from '@/store/auth';
import { toast } from '@/store/toast';

const KEY = 'follows';

export function useFollowSuggestions(limit = 8) {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: [KEY, 'suggestions', limit],
    queryFn: () => followsApi.getFollowSuggestions(limit),
    enabled: Boolean(token),
    staleTime: 30_000,
  });
}

export function useMyFollowing() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: [KEY, 'following'],
    queryFn: () => followsApi.getMyFollowing(),
    enabled: Boolean(token),
    staleTime: 30_000,
  });
}

export function useMyFriends() {
  const token = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: [KEY, 'friends'],
    queryFn: () => followsApi.getMyFriends(),
    enabled: Boolean(token),
    staleTime: 30_000,
  });
}

export function useFollowCounts(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'counts', id],
    queryFn: () => followsApi.getFollowCounts(id as string),
    enabled: Boolean(id),
    staleTime: 30_000,
  });
}

export function useFollowAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, following }: { id: string; following: boolean }) =>
      following ? followsApi.unfollowUser(id) : followsApi.followUser(id),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success(vars.following ? 'Berhenti mengikuti' : 'Mulai mengikuti');
    },
  });
}
