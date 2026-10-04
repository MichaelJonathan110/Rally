import { useQuery } from '@tanstack/react-query';
import * as catalogApi from '@/api/catalog';

/** The city list with activity counts - powers onboarding + the header picker. */
export function useCities() {
  return useQuery({
    queryKey: ['cities'],
    queryFn: catalogApi.listCities,
    staleTime: 5 * 60_000,
  });
}

/** The activity-type registry - powers the "jenis kegiatan" filter. */
export function useActivityTypes() {
  return useQuery({
    queryKey: ['activity-types'],
    queryFn: catalogApi.listActivityTypes,
    staleTime: 30 * 60_000,
  });
}
