import { Link, useParams } from 'react-router-dom';
import { MapPin, Clock } from 'lucide-react';
import { useVenue, useVenueCourts } from '@/hooks/useVenues';
import { Badge } from '@/components/ui/Badge';
import { Card, CardHeader } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCents } from '@/lib/utils';
import { cleanDescription } from '@/lib/format';

export default function VenueDetail() {
  const { id = '' } = useParams();
  const venue = useVenue(id);
  const courts = useVenueCourts(id);

  if (venue.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }
  if (venue.isError || !venue.data) {
    return <ErrorState title="Venue tidak ditemukan" onRetry={() => venue.refetch()} />;
  }

  const v = venue.data;
  return (
    <div className="space-y-5">
      <Link to="/venues" className="text-sm text-ink-3 hover:text-action">
        &larr; Semua venue
      </Link>
      <div className="card space-y-3 p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="text-2xl font-bold text-ink">{v.name}</h1>
          <Badge tone="success">{v.court_count} lapangan</Badge>
        </div>
        <p className="flex items-center gap-2 text-sm text-ink-2">
          <MapPin className="h-4 w-4" />
          {[v.address_line, v.city, v.country].filter(Boolean).join(', ')}
        </p>
        {cleanDescription(v.description, v.name) ? (
          <p className="text-sm text-ink-3">{cleanDescription(v.description, v.name)}</p>
        ) : null}
      </div>

      <Card>
        <CardHeader title="Lapangan" subtitle="Ketersediaan dan harga" />
        {courts.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : courts.data && courts.data.length > 0 ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {courts.data.map((c) => (
              <div key={c.id} className="rounded-xl border border-line bg-paper/60 p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-ink">{c.name}</h3>
                  <Badge tone="accent">{formatCents(c.hourly_price_cents)}/jam</Badge>
                </div>
                <p className="mt-2 text-sm text-ink-3">
                  {c.surface || 'Permukaan standar'} &middot; hingga {c.capacity} pemain
                </p>
                {c.availability.length > 0 ? (
                  <p className="mt-2 flex items-center gap-1.5 text-xs text-ink-3">
                    <Clock className="h-3.5 w-3.5" />
                    {c.availability.length} slot tersedia
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="Belum ada lapangan" description="Venue ini belum punya lapangan." />
        )}
      </Card>
    </div>
  );
}
