import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Bell, LogOut, Menu, Search } from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import { useLogout } from '@/hooks/useAuth';
import { useNotifications } from '@/hooks/useLeaderboard';
import { Avatar } from '@/components/ui/Avatar';
import Logo from '@/components/brand/Logo';
import { CitySelector } from '@/components/city/CityPicker';
import { LangToggle } from './LangToggle';
import { useT } from '@/i18n/strings';

export function TopBar({ onMenu }: { onMenu?: () => void }) {
  const t = useT();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.accessToken);
  const logout = useLogout();
  const navigate = useNavigate();
  const notifs = useNotifications(true);
  const unread = token ? notifs.data?.unread_count ?? notifs.data?.total ?? 0 : 0;

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 w-full max-w-[1180px] items-center gap-2 px-4 sm:h-16 sm:px-6">
        <button
          onClick={onMenu}
          aria-label="Buka menu"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-ink-2 hover:bg-ink/[0.05] lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>

        <Link to="/" className="flex items-center gap-2 lg:hidden" aria-label="RALLY - Beranda">
          <Logo size={26} tone="ink" variant="mark" />
        </Link>

        <button
          onClick={() => navigate('/discover')}
          className="ml-auto flex h-10 flex-1 items-center gap-2 rounded-full border border-line bg-surface px-3.5 text-sm text-ink-3 transition-colors hover:border-ink/20 hover:text-ink sm:max-w-sm lg:ml-0"
        >
          <Search className="h-4 w-4 shrink-0" />
          <span className="line-clamp-1">{t('nav.search')}</span>
        </button>

        <LangToggle className="hidden sm:inline-flex" />
        <CitySelector className="hidden sm:block" />

        <button
          onClick={() => navigate('/profile')}
          aria-label={`Notifikasi${unread > 0 ? `, ${unread} belum dibaca` : ''}`}
          className="relative ml-auto inline-flex h-10 w-10 items-center justify-center rounded-xl text-ink-2 hover:bg-ink/[0.05] lg:ml-0"
        >
          <Bell className="h-5 w-5" />
          {unread > 0 ? (
            <span className="absolute right-1.5 top-1.5 grid h-4 min-w-4 place-items-center rounded-full bg-action px-1 text-[10px] font-bold text-ink">
              {unread > 9 ? '9+' : unread}
            </span>
          ) : null}
        </button>

        {token && user ? (
          <div className="flex items-center gap-1.5">
            <NavLink to="/profile" className="hidden sm:block" aria-label="Profil saya">
              <Avatar name={user.username} src={user.profile?.avatar_url ?? undefined} size={34} />
            </NavLink>
            <button
              aria-label="Keluar"
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl text-ink-2 hover:bg-ink/[0.05]"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            className="inline-flex h-10 items-center rounded-full bg-action px-4 text-sm font-bold text-ink transition-colors hover:bg-action-dark"
          >
            Masuk
          </Link>
        )}
      </div>
    </header>
  );
}
