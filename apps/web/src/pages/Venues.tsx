import { useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Search } from 'lucide-react';
import { useVenues } from '@/hooks/useVenues';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { cleanDescription } from '@/lib/format';

export default function Venues() {
  const [term, setTerm] = useState('');
  const { data, isLoading, isError, refetch } = useVenues({ search: term || undefined, limit: 24 });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Venue</h1>
        <p className="mt-1 text-sm text-ink-3">Lapangan dan venue siap dipesan di seluruh Indonesia.</p>
      </div>
      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-3" />
        <Input
          aria-label="Cari venue"
          placeholder="Cari nama atau kota..."
          className="pl-9"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
        />
      </div>
      {isLoading ? (
        <SkeletonList count={6} />
      ) : isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : data && data.items.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((v) => (
            <Link key={v.id} to={`/venues/${v.id}`} className="card p-4 hover:border-action/40">
              <div className="flex items-start justify-between gap-2">
                <h3 className="line-clamp-1 font-semibold text-ink">{v.name}</h3>
                <Badge tone="success">{v.court_count} lapangan</Badge>
              </div>
              <p className="mt-2 flex items-center gap-1.5 text-sm text-ink-3">
                <MapPin className="h-4 w-4" /> {v.city}
                {v.country ? `, ${v.country}` : ''}
              </p>
              {cleanDescription(v.description, v.name) ? (
                <p className="mt-2 line-clamp-2 text-sm text-ink-3">
                  {cleanDescription(v.description, v.name)}
                </p>
              ) : null}
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState title="Venue tidak ditemukan" description="Coba kata kunci lain." />
      )}
    </div>
  );
}
