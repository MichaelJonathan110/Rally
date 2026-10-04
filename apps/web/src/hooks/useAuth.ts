import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as authApi from '@/api/auth';
import { updateMe, type UserUpdateInput } from '@/api/users';
import type { AuthResponse } from '@/api/types';
import { useAuthStore } from '@/store/auth';
import { toast } from '@/store/toast';

export function useAuth() {
  const { user, accessToken, setSession, setUser, clear } = useAuthStore();
  return { user, isAuthenticated: Boolean(accessToken), setSession, setUser, clear };
}

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation<AuthResponse, unknown, authApi.LoginInput>({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setSession(data.user, data.tokens.access_token, data.tokens.refresh_token);
      toast.success('Selamat datang kembali', data.user.username);
    },
  });
}

export function useRegister() {
  const setSession = useAuthStore((s) => s.setSession);
  return useMutation<AuthResponse, unknown, authApi.RegisterInput>({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setSession(data.user, data.tokens.access_token, data.tokens.refresh_token);
      toast.success('Akun dibuat', data.user.username);
    },
  });
}

export function useMe() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery({
    queryKey: ['me', accessToken],
    queryFn: async () => {
      const user = await authApi.me();
      setUser(user);
      return user;
    },
    enabled: Boolean(accessToken),
    staleTime: 60_000,
  });
}

export function useUpdateMe() {
  const setUser = useAuthStore((s) => s.setUser);
  return useMutation({
    mutationFn: (input: UserUpdateInput) => updateMe(input),
    onSuccess: (user) => setUser(user),
  });
}

export function useLogout() {
  const clear = useAuthStore((s) => s.clear);
  const qc = useQueryClient();
  return () => {
    clear();
    qc.clear();
    toast.info('Berhasil keluar');
  };
}

export function useForgotPassword() {
  return useMutation<{ message: string }, unknown, string>({
    mutationFn: (email: string) => authApi.forgotPassword(email),
  });
}

export function useResetPassword() {
  return useMutation<
    { message: string },
    unknown,
    { token: string; newPassword: string }
  >({
    mutationFn: ({ token, newPassword }) => authApi.resetPassword(token, newPassword),
    onSuccess: () => toast.success('Kata sandi diperbarui', 'Silakan masuk dengan kata sandi baru.'),
  });
}

export function useResendVerification() {
  return useMutation<{ message: string }, unknown, void>({
    mutationFn: () => authApi.resendVerification(),
    onSuccess: (data) =>
      toast.success('Email verifikasi terkirim', data.message || 'Cek kotak masuk emailmu.'),
    onError: () => toast.error('Gagal mengirim email', 'Coba lagi sebentar lagi.'),
  });
}
