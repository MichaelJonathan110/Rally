import api from './client';
import type { AuthResponse, User } from './types';

export interface LoginInput {
  email?: string;
  username?: string;
  password: string;
}
export interface RegisterInput {
  email: string;
  username: string;
  password: string;
}
export interface MessageResponse {
  message: string;
}

export async function login(input: LoginInput): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/api/v1/auth/login', input);
  return data;
}

export async function register(input: RegisterInput): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/api/v1/auth/register', input);
  return data;
}

export async function me(): Promise<User> {
  const { data } = await api.get<User>('/api/v1/auth/me');
  return data;
}

/** Request a password-reset link. Always answered with 200 (no enumeration). */
export async function forgotPassword(email: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/api/v1/auth/forgot-password', { email });
  return data;
}

/** Complete a password reset with the emailed token. */
export async function resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/api/v1/auth/reset-password', {
    token,
    new_password: newPassword,
  });
  return data;
}

/** Confirm an email address with the emailed verification token. */
export async function verifyEmail(token: string): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/api/v1/auth/verify-email', { token });
  return data;
}

/** Re-send the verification email to the signed-in user. */
export async function resendVerification(): Promise<MessageResponse> {
  const { data } = await api.post<MessageResponse>('/api/v1/auth/resend-verification');
  return data;
}
