import api from './client';
import { API_URL } from '@/config/brand';

/** Metadata returned by POST /api/v1/media/upload. */
export interface MediaUploadResult {
  url: string;
  filename: string;
  size: number;
  content_type: string;
}

/** Purposes accepted by the backend media service. */
export type MediaPurpose = 'avatar' | 'activity' | 'venue' | 'review';

/**
 * Upload one image. The browser sets the multipart boundary itself, so we never
 * touch the Content-Type header here (the auth token comes from the shared
 * axios interceptor).
 */
export async function uploadFile(file: File, purpose: MediaPurpose): Promise<MediaUploadResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('purpose', purpose);
  const { data } = await api.post<MediaUploadResult>('/api/v1/media/upload', form);
  return data;
}

/**
 * Resolve a stored relative '/media/...' path to an absolute URL against the
 * API origin. Already-absolute (http/https/data/blob) values pass through.
 */
export function resolveMediaUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  if (/^(https?:|data:|blob:)/i.test(url)) return url;
  return `${API_URL.replace(/\/+$/, '')}/${url.replace(/^\/+/, '')}`;
}
