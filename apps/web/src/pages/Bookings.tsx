import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { CalendarCheck, CreditCard, XCircle, Plus } from 'lucide-react';
import { useMyBookings, useCancelBooking, usePayBooking, useCreateBooking } from '@/hooks/useBookings';
import { useVenues } from '@/hooks/useVenues';
import * as venuesApi from '@/api/venues';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { formatCents } from '@/lib/utils';
import { extractDetail } from '@/api/client';

const statusTone: Record<string, 'neutral' | 'accent' | 'success' | 'danger' | 'warning'> = {
  pending: 'warning',
  confirmed: 'success',
  cancelled: 'danger',
  completed: 'neutral',
  refunded: 'neutral',
};

export default function Bookings() {
  const bookings = useMyBookings();
  const cancel = useCancelBooking();
  const pay = usePayBooking();
  const create = useCreateBooking();

  const [open, setOpen] = useState(false);
  const [venueId, setVenueId] = useState('');
  const [courtId, setCourtId] = useState('');
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [total, setTotal] = useState('');

  const venues = useVenues({ limit: 100 });
  const courts = useQuery({
    queryKey: ['venue-courts', venueId],
    queryFn: () => venuesApi.listCourts(venueId),
    enabled: Boolean(venueId),
  });

  const selectedCourt = courts.data?.find((c) => c.id === courtId);

  const submit = () => {
    create.mutate(
      {
        venue_court_id: courtId || null,
        starts_at: new Date(startsAt).toISOString(),
        ends_at: new Date(endsAt).toISOString(),
        total_price_cents: total ? Math.round(Number(total)) : undefined,
        idempotency_key: `ui-${Date.now()}`,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setCourtId('');
          setStartsAt('');
          setEndsAt('');
          setTotal('');
        },
      },
    );
  };

  const canSubmit = Boolean(courtId && startsAt && endsAt && new Date(endsAt) > new Date(startsAt));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">Pesanan saya</h1>
          <p className="mt-1 text-sm text-ink-3">Reservasi lapangan dan patungan biaya.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> Pesanan baru
        </Button>
      </div>

      {bookings.isLoading ? (
        <SkeletonList count={3} />
      ) : bookings.isError ? (
        <ErrorState onRetry={() => bookings.refetch()} />
      ) : bookings.data && bookings.data.items.length > 0 ? (
        <div className="space-y-3">
          {bookings.data.items.map((b) => (
            <Card key={b.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge tone={statusTone[b.status] ?? 'neutral'}>{b.status}</Badge>
                    <span className="text-sm text-ink-3">
                      {b.venue_court_id ? 'Pesanan lapangan' : 'Pesanan kegiatan'}
                    </span>
                  </div>
                  <p className="mt-2 flex items-center gap-2 text-sm text-ink">
                    <CalendarCheck className="h-4 w-4 text-ink-3" />
                    {format(new Date(b.starts_at), 'EEE d MMM HH:mm')} &ndash;{' '}
                    {format(new Date(b.ends_at), 'HH:mm')}
                  </p>
                  <p className="mt-1 text-sm font-semibold text-action">
                    {formatCents(b.total_price_cents, b.currency)}
                    {b.payments.length > 0 ? ` · ${b.payments.length} pembayaran` : ''}
                  </p>
                </div>

                <div className="flex gap-2">
                  {b.status !== 'cancelled' && b.status !== 'completed' ? (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        loading={pay.isPending}
                        onClick={() => pay.mutate({ id: b.id, key: `pay-${b.id}` })}
                      >
                        <CreditCard className="h-4 w-4" /> Bayar
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        loading={cancel.isPending}
                        onClick={() => cancel.mutate(b.id)}
                      >
                        <XCircle className="h-4 w-4" /> Batal
                      </Button>
                    </>
                  ) : null}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="Belum ada pesanan"
          description="Pesan lapangan dan ajak teman untuk patungan."
          action={<Button onClick={() => setOpen(true)}>Buat pesanan</Button>}
        />
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="Pesanan baru">
        <div className="space-y-4">
          <Select
            label="Venue"
            options={[
              { value: '', label: 'Pilih venue' },
              ...(venues.data?.items.map((v) => ({ value: v.id, label: `${v.name} - ${v.city}` })) ?? []),
            ]}
            value={venueId}
            onChange={(e) => {
              setVenueId(e.target.value);
              setCourtId('');
            }}
          />
          <Select
            label="Lapangan"
            disabled={!venueId}
            options={[
              { value: '', label: venueId ? 'Pilih lapangan' : 'Pilih venue dulu' },
              ...(courts.data?.map((c) => ({
                value: c.id,
                label: `${c.name} - ${formatCents(c.hourly_price_cents)}/jam`,
              })) ?? []),
            ]}
            value={courtId}
            onChange={(e) => setCourtId(e.target.value)}
          />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input
              label="Mulai"
              type="datetime-local"
              value={startsAt}
              onChange={(e) => setStartsAt(e.target.value)}
            />
            <Input
              label="Selesai"
              type="datetime-local"
              value={endsAt}
              onChange={(e) => setEndsAt(e.target.value)}
            />
          </div>
          <Input
            label="Total harga (Rp, opsional)"
            type="number"
            step="1"
            min={0}
            placeholder={
              selectedCourt ? `Otomatis: ${formatCents(selectedCourt.hourly_price_cents)}/jam` : 'Otomatis dari lapangan'
            }
            value={total}
            onChange={(e) => setTotal(e.target.value)}
          />
          {create.isError ? (
            <p className="text-sm text-danger" role="alert">
              {extractDetail(create.error)}
            </p>
          ) : null}
          <div className="flex gap-3">
            <Button fullWidth disabled={!canSubmit} loading={create.isPending} onClick={submit}>
              Create booking
            </Button>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
