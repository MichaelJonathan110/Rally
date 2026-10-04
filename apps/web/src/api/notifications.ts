import api from './client';
import type { NotificationPage } from './types';

export async function listNotifications(unreadOnly = false): Promise<NotificationPage> {
  const { data } = await api.get<NotificationPage>('/api/v1/notifications', {
    params: { unread_only: unreadOnly },
  });
  return data;
}

export async function markRead(id: string): Promise<void> {
  await api.post(`/api/v1/notifications/${id}/read`);
}
