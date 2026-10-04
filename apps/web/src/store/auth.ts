import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/api/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  setSession: (user: User, accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  clear: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setSession: (user, accessToken, refreshToken) =>
        set({ user, accessToken, refreshToken }),
      setUser: (user) => set({ user }),
      clear: () => set({ user: null, accessToken: null, refreshToken: null }),
      isAuthenticated: () => Boolean(get().accessToken),
    }),
    { name: 'rally.auth' },
  ),
);

/** Read the token without subscribing (used by the axios interceptor). */
export const getAccessToken = (): string | null => useAuthStore.getState().accessToken;
export const getRefreshToken = (): string | null => useAuthStore.getState().refreshToken;
