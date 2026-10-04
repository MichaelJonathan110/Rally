import api from './client';
import type { Balance, Booking, BookingCreateInput, Page, Payment } from './types';

export async function listMyBookings(): Promise<Page<Booking>> {
  const { data } = await api.get<Page<Booking>>('/api/v1/bookings', { params: { mine: true } });
  return data;
}

export async function getBooking(id: string): Promise<Booking> {
  const { data } = await api.get<Booking>(`/api/v1/bookings/${id}`);
  return data;
}

export async function createBooking(input: BookingCreateInput): Promise<Booking> {
  const { data } = await api.post<Booking>('/api/v1/bookings', input);
  return data;
}

export async function cancelBooking(id: string): Promise<Booking> {
  const { data } = await api.post<Booking>(`/api/v1/bookings/${id}/cancel`);
  return data;
}

export async function getBalance(id: string): Promise<Balance> {
  const { data } = await api.get<Balance>(`/api/v1/bookings/${id}/balance`);
  return data;
}

export async function payBooking(id: string, idempotencyKey: string): Promise<Payment> {
  const { data } = await api.post<Payment>(`/api/v1/bookings/${id}/pay`, {
    idempotency_key: idempotencyKey,
  });
  return data;
}
