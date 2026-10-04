import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
type Size = 'sm' | 'md' | 'lg' | 'icon';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  fullWidth?: boolean;
}

/* Deep coral is the single "do this" colour. Ink text keeps it WCAG AA
   (6.7:1) - white on coral would only be 2.8:1. */
const variants: Record<Variant, string> = {
  primary:
    'bg-action text-ink font-bold hover:bg-action-dark active:translate-y-px shadow-pop disabled:bg-action/40',
  secondary: 'bg-ink text-ink-inv hover:bg-ink/90 active:translate-y-px',
  ghost: 'bg-transparent text-ink-2 hover:bg-ink/[0.05] hover:text-ink',
  danger: 'bg-danger text-ink font-semibold hover:bg-danger/90',
  outline: 'border border-line bg-surface text-ink hover:border-ink/25 hover:bg-ink/[0.03]',
};

const sizes: Record<Size, string> = {
  sm: 'h-9 px-3.5 text-sm',
  md: 'h-11 px-5 text-sm',
  lg: 'h-12 px-6 text-base',
  icon: 'h-11 w-11',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', size = 'md', loading, fullWidth, className, children, disabled, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        'inline-flex select-none items-center justify-center gap-2 rounded-full font-semibold transition-all duration-200 ease-spring',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-action focus-visible:ring-offset-2 focus-visible:ring-offset-paper',
        'disabled:cursor-not-allowed disabled:opacity-60',
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        className,
      )}
      {...rest}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
      {children}
    </button>
  );
});
