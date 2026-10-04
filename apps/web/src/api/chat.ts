import api from './client';
import { API_URL } from '@/config/brand';
import { getAccessToken } from '@/store/auth';
import type { UUID } from './types';

/**
 * Chat transport: rooms, messages and the real-time WebSocket stream.
 *
 * Mirrors app/schemas/chat.py exactly (snake_case wire format). The backend
 * owns chat_rooms / chat_messages and exposes:
 *   GET  /api/v1/chat/rooms
 *   GET  /api/v1/chat/rooms/{room_id}
 *   GET  /api/v1/chat/rooms/{room_id}/messages?limit=&offset=
 *   POST /api/v1/chat/rooms/{room_id}/messages
 *   WS   /api/v1/chat/ws?room_id=<uuid>&token=<jwt>
 */

export type ChatRoomType = 'direct' | 'group' | 'activity' | 'club' | 'tournament';

export interface ChatRoom {
  id: UUID;
  type: ChatRoomType;
  name: string | null;
  activity_id: UUID | null;
  club_id: UUID | null;
  last_message_at: string | null;
  unread_count: number;
  created_at: string;
}

export interface ChatMessage {
  id: UUID;
  room_id: UUID;
  sender_id: UUID;
  sender_name: string | null;
  body: string;
  created_at: string;
}

export interface ChatRoomPage {
  items: ChatRoom[];
  total: number;
}

export interface ChatMessagePage {
  items: ChatMessage[];
  total: number;
}

export interface MessageFilters {
  limit?: number;
  offset?: number;
}

/** A frame pushed by the room WebSocket. */
export interface ChatSocketEvent {
  type: 'message';
  message: ChatMessage;
}

export async function listRooms(): Promise<ChatRoomPage> {
  const { data } = await api.get<ChatRoomPage>('/api/v1/chat/rooms');
  return data;
}

export async function getRoom(id: UUID): Promise<ChatRoom> {
  const { data } = await api.get<ChatRoom>(`/api/v1/chat/rooms/${id}`);
  return data;
}

export async function listMessages(
  roomId: UUID,
  filters: MessageFilters = {},
): Promise<ChatMessagePage> {
  const { data } = await api.get<ChatMessagePage>(`/api/v1/chat/rooms/${roomId}/messages`, {
    params: filters,
  });
  return data;
}

export async function sendMessage(roomId: UUID, body: string): Promise<ChatMessage> {
  const { data } = await api.post<ChatMessage>(`/api/v1/chat/rooms/${roomId}/messages`, {
    body,
  });
  return data;
}

/** Derive the WS origin from the API URL when VITE_WS_URL is not provided. */
const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? API_URL.replace(/^http/, 'ws');

/** Authenticated WebSocket URL for a room, carrying the current access token. */
export function wsUrl(roomId: UUID): string {
  const token = getAccessToken() ?? '';
  const base = WS_URL.replace(/\/+$/, '');
  return `${base}/api/v1/chat/ws?room_id=${encodeURIComponent(roomId)}&token=${encodeURIComponent(token)}`;
}
