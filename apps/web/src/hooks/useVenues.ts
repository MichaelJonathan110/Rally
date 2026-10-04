import { useQuery } from '@tanstack/react-query';
import * as venuesApi from '@/api/venues';

const KEY = 'venues';

export function useVenues(filters: venuesApi.VenueFilters = {}) {
  return useQuery({
    queryKey: [KEY, filters],
    queryFn: () => venuesApi.listVenues(filters),
    staleTime: 30_000,
  });
}

export function useVenue(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'detail', id],
    queryFn: () => venuesApi.getVenue(id as string),
    enabled: Boolean(id),
  });
}

export function useVenueCourts(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'courts', id],
    queryFn: () => venuesApi.listCourts(id as string),
    enabled: Boolean(id),
  });
}
