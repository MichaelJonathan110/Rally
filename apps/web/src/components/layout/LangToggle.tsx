import { cn } from '@/lib/utils';
import { useLangStore, type Lang } from '@/i18n/strings';

const OPTIONS: { value: Lang; label: string }[] = [
  { value: 'id', label: 'ID' },
  { value: 'en', label: 'EN' },
];

export function LangToggle({ className }: { className?: string }) {
  const lang = useLangStore((s) => s.lang);
  const setLang = useLangStore((s) => s.setLang);
  return (
    <div
      role="group"
      aria-label="Bahasa / Language"
      className={cn('inline-flex h-10 items-center rounded-full border border-line bg-surface p-0.5', className)}
    >
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => setLang(o.value)}
          aria-pressed={lang === o.value}
          className={cn(
            'inline-flex h-9 min-w-[2.25rem] items-center justify-center rounded-full px-2 text-xs font-bold transition-colors',
            lang === o.value ? 'bg-ink text-ink-inv' : 'text-ink-3 hover:text-ink',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
