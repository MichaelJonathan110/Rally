import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { PRIMARY_NAV, SECONDARY_NAV } from '@/config/nav';
import Logo from '@/components/brand/Logo';
import { useAuthStore } from '@/store/auth';
import { Avatar } from '@/components/ui/Avatar';

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((s) => s.user);

  const render = (items: typeof PRIMARY_NAV) =>
    items.map((item) => {
      const Icon = item.icon;
      return (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === '/'}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'group flex min-h-[44px] items-center gap-3 rounded-xl px-3 text-sm font-semibold transition-all duration-200',
              isActive
                ? 'bg-ink text-ink-inv shadow-soft'
                : 'text-ink-2 hover:bg-ink/[0.05] hover:text-ink',
            )
          }
        >
          {({ isActive }) => (
            <>
              <Icon className={cn('h-[18px] w-[18px] shrink-0', isActive && 'text-ink-inv')} />
              <span className="line-clamp-1">{item.label}</span>
            </>
          )}
        </NavLink>
      );
    });

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center px-5">
        <NavLink to="/" onClick={onNavigate} aria-label="RALLY - Beranda">
          <Logo size={30} tone="ink" />
        </NavLink>
      </div>

      <nav aria-label="Navigasi utama" className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 pb-3">
        {render(PRIMARY_NAV)}
        <p className="mt-4 px-3 text-2xs font-bold uppercase tracking-[0.16em] text-ink-3">
          Komunitas
        </p>
        {render(SECONDARY_NAV)}
      </nav>

      <div className="border-t border-line p-3">
        {user ? (
          <NavLink
            to="/profile"
            onClick={onNavigate}
            className="flex items-center gap-3 rounded-xl p-2 transition-colors hover:bg-ink/[0.05]"
          >
            <Avatar name={user.username} src={user.profile?.avatar_url ?? undefined} size={36} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">
                {user.profile?.display_name ?? user.username}
              </p>
              <p className="truncate text-xs text-ink-3">{user.profile?.city ?? 'Indonesia'}</p>
            </div>
          </NavLink>
        ) : (
          <NavLink
            to="/login"
            onClick={onNavigate}
            className="flex min-h-[44px] items-center justify-center rounded-xl bg-action px-4 text-sm font-bold text-ink transition-colors hover:bg-action-dark"
          >
            Masuk
          </NavLink>
        )}
      </div>
    </div>
  );
}
