import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import { API_URL } from '@/config/brand';
import { toast } from '@/store/toast';
import { useAuthStore } from '@/store/auth';

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 20000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const res = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token } = res.data as {
      access_token: string;
      refresh_token: string;
    };
    const user = useAuthStore.getState().user;
    if (user) useAuthStore.getState().setSession(user, access_token, refresh_token);
    return access_token;
  } catch {
    return null;
  }
}

const DETAIL_ID: Record<string, string> = {
  'Activity not found': 'Kegiatan tidak ditemukan.',
  'Tournament not found': 'Turnamen tidak ditemukan.',
  'Venue not found': 'Venue tidak ditemukan.',
  'Club not found': 'Komunitas tidak ditemukan.',
  'User not found': 'Pengguna tidak ditemukan.',
  'Not found': 'Data tidak ditemukan.',
  'Unauthorized': 'Sesi berakhir. Silakan masuk lagi.',
  'Forbidden': 'Kamu tidak punya akses ke aksi ini.',
  'Internal Server Error': 'Terjadi kesalahan pada server.',
};

function localiseDetail(detail: string): string {
  return DETAIL_ID[detail] ?? detail;
}

function extractDetail(error: unknown): string {
  const err = error as AxiosError;
  const data = err.response?.data as { detail?: unknown; message?: string } | undefined;
  if (data?.detail) {
    if (typeof data.detail === 'string') return localiseDetail(data.detail);
    if (Array.isArray(data.detail)) {
      const first = data.detail[0] as { msg?: string } | undefined;
      if (first?.msg) return localiseDetail(first.msg);
    }
  }
  if (data?.message) return localiseDetail(data.message);
  return err.message ?? "Permintaan gagal";
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const status = error.response?.status;
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retried?: boolean })
      | undefined;

    if (status === 401 && original && !original._retried) {
      original._retried = true;
      // Only a request that carried a session can be "expired". A 401 on an
      // anonymous request (e.g. a protected endpoint polled while signed out)
      // must NOT force a redirect, otherwise public pages bounce to /login.
      const hadSession = Boolean(useAuthStore.getState().accessToken);
      if (!hadSession) {
        return Promise.reject(error);
      }
      refreshing = refreshing ?? refreshAccessToken();
      const token = await refreshing;
      refreshing = null;
      if (token) {
        original.headers.set('Authorization', `Bearer ${token}`);
        return api(original);
      }
      useAuthStore.getState().clear();
      toast.error('Sesi berakhir', 'Silakan masuk lagi.');
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.assign('/login');
      }
      return Promise.reject(error);
    }

    if (status !== 401) {
      toast.error('Permintaan gagal', extractDetail(error));
    }
    return Promise.reject(error);
  },
);

export { extractDetail };
export default api;
