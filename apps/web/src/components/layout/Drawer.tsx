import { useEffect, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { LogoWordmark } from '@/components/brand/Logo';

export function Drawer({
  open,
  onClose,
  children,
}: {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  return (
    <div className={open ? '' : 'pointer-events-none'}>
      <div
        className={
          'fixed inset-0 z-40 bg-ink/40 transition-opacity duration-300 lg:hidden ' +
          (open ? 'opacity-100' : 'opacity-0')
        }
        onClick={onClose}
        aria-hidden
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Menu navigasi"
        className={
          'fixed inset-y-0 left-0 z-50 flex w-72 max-w-[82vw] flex-col border-r border-line bg-paper transition-transform duration-300 ease-spring lg:hidden ' +
          (open ? 'translate-x-0' : '-translate-x-full')
        }
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        <div className="flex h-14 items-center justify-between px-4">
          <LogoWordmark size={20} tone="ink" />
          <button
            onClick={onClose}
            aria-label="Tutup menu"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-ink-2 hover:bg-ink/[0.05]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}
