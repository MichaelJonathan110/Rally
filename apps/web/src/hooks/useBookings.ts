import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as bookingsApi from '@/api/bookings';
import type { Booking, BookingCreateInput } from '@/api/types';
import { toast } from '@/store/toast';

const KEY = 'bookings';

export function useMyBookings() {
  return useQuery({
    queryKey: [KEY, 'mine'],
    queryFn: bookingsApi.listMyBookings,
    staleTime: 10_000,
  });
}

export function useCreateBooking() {
  const qc = useQueryClient();
  return useMutation<Booking, unknown, BookingCreateInput>({
    mutationFn: bookingsApi.createBooking,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success('Booking dibuat');
    },
  });
}

export function useCancelBooking() {
  const qc = useQueryClient();
  return useMutation<Booking, unknown, string>({
    mutationFn: (id) => bookingsApi.cancelBooking(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.info('Booking dibatalkan');
    },
  });
}

export function useBalance(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, 'balance', id],
    queryFn: () => bookingsApi.getBalance(id as string),
    enabled: Boolean(id),
  });
}

export function usePayBooking() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, key }: { id: string; key: string }) => bookingsApi.payBooking(id, key),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY] });
      toast.success('Pembayaran berhasil (provider mock)');
    },
  });
}
