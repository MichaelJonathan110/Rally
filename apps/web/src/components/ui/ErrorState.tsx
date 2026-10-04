import { AlertTriangle } from 'lucide-react';
import { Button } from './Button';

export function ErrorState({
  title,
  message,
  onRetry,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-danger/30 bg-danger/5 px-6 py-12 text-center">
      <AlertTriangle className="h-8 w-8 text-danger" />
      <div>
        {title ? <p className="font-semibold text-ink">{title}</p> : null}
        <p className="text-sm text-ink-2">
          {message ?? 'Terjadi kesalahan saat menghubungi server.'}
        </p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Coba lagi
        </Button>
      ) : null}
    </div>
  );
}
