import { CheckCircle2, Info, XCircle, X } from 'lucide-react';
import { useToastStore, type ToastVariant } from '@/store/toast';
import { cn } from '@/lib/utils';

const icons: Record<ToastVariant, typeof Info> = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

const tones: Record<ToastVariant, string> = {
  success: 'text-success',
  error: 'text-danger',
  info: 'text-action',
};

export function ToastViewport() {
  const { toasts, dismiss } = useToastStore();
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-[calc(env(safe-area-inset-bottom)+4.5rem)] z-[60] flex flex-col items-center gap-2 px-4 sm:bottom-4 sm:left-auto sm:right-4 sm:items-end">
      {toasts.map((t) => {
        const Icon = icons[t.variant];
        return (
          <div
            key={t.id}
            role="status"
            className="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border border-line bg-surface-muted/95 p-3 shadow-xl backdrop-blur"
          >
            <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', tones[t.variant])} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-ink">{t.title}</p>
              {t.description ? (
                <p className="mt-0.5 text-xs text-ink-2">{t.description}</p>
              ) : null}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              aria-label="Tutup"
              className="rounded-lg p-1 text-ink-3 hover:bg-ink/[0.04]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
