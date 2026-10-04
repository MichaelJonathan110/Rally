import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as tApi from '@/api/tournaments';
import { toast } from '@/store/toast';

const KEY = 'tournaments';

export function useTournaments(filters: tApi.TournamentFilters = {}) {
  return useQuery({
    queryKey: [KEY, filters],
    queryFn: () => tApi.listTournaments(filters),
    staleTime: 20_000,
  });
}

export function useTournament(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'detail', id],
    queryFn: () => tApi.getTournament(id as string),
    enabled: Boolean(id),
  });
}

export function useTournamentEntries(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'entries', id],
    queryFn: () => tApi.listEntries(id as string),
    enabled: Boolean(id),
  });
}

export function useTournamentStandings(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'standings', id],
    queryFn: () => tApi.getStandings(id as string),
    enabled: Boolean(id),
  });
}

export function useTournamentBracket(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'bracket', id],
    queryFn: () => tApi.getBracket(id as string),
    enabled: Boolean(id),
  });
}

export function useRegisterTournament(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => tApi.registerForTournament(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success('Terdaftar di turnamen');
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error('Gagal mendaftar', detail ?? 'Coba lagi sebentar lagi.');
    },
  });
}
