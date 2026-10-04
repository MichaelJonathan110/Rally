import { useState, type ReactNode } from 'react';
import { TopBar } from './TopBar';
import { BottomNav } from './BottomNav';
import { Drawer } from './Drawer';
import { SidebarNav } from './SidebarNav';
import { EmailVerifyBanner } from './EmailVerifyBanner';

export function AppShell({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="min-h-dvh text-ink">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-ink-inv"
      >
        Lompat ke konten
      </a>

      <div className="flex">
        <aside className="sticky top-0 hidden h-dvh w-[17rem] shrink-0 flex-col border-r border-line bg-paper-warm/50 lg:flex">
          <SidebarNav />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar onMenu={() => setDrawerOpen(true)} />
          <main
            id="main"
            className="mx-auto w-full max-w-[1180px] flex-1 px-4 py-5 pb-[calc(env(safe-area-inset-bottom)+5.5rem)] sm:px-6 sm:py-7 lg:pb-10"
          >
            <EmailVerifyBanner />
            {children}
          </main>
        </div>
      </div>

      <Drawer open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <SidebarNav onNavigate={() => setDrawerOpen(false)} />
      </Drawer>

      <BottomNav />
    </div>
  );
}
