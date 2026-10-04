import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { PRIMARY_NAV } from '@/config/nav';

export function BottomNav() {
  return (
    <nav
      aria-label="Navigasi bawah"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-paper/95 backdrop-blur-md lg:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <ul className="mx-auto flex max-w-lg items-stretch justify-between px-1.5">
        {PRIMARY_NAV.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.to} className="flex-1">
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'relative flex min-h-[58px] flex-col items-center justify-center gap-1 px-1 py-1.5 text-[11px] font-semibold transition-colors',
                    isActive ? 'text-ink' : 'text-ink-3',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span
                      className={cn(
                        'grid h-8 w-8 place-items-center rounded-xl transition-all duration-300 ease-spring',
                        isActive ? 'bg-action text-ink shadow-pop' : 'bg-transparent',
                      )}
                    >
                      <Icon className="h-[18px] w-[18px]" />
                    </span>
                    <span>{item.label}</span>
                  </>
                )}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
