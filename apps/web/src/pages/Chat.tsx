import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { MessageSquare, Send, Wifi, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Avatar } from '@/components/ui/Avatar';
import { PageHeader } from '@/components/ui/PageHeader';
import { cn } from '@/lib/utils';
import { clock, relative, dateTime } from '@/lib/format';
import { useAuthStore } from '@/store/auth';
import { toast } from '@/store/toast';
import * as chatApi from '@/api/chat';
import type { ChatMessage, ChatRoom, ChatSocketEvent } from '@/api/chat';

const ROOMS_KEY = ['chat', 'rooms'];

function roomLabel(room: ChatRoom): string {
  if (room.name) return room.name;
  switch (room.type) {
    case 'activity':
      return 'Ruang kegiatan';
    case 'club':
      return 'Ruang komunitas';
    case 'tournament':
      return 'Ruang turnamen';
    case 'group':
      return 'Obrolan grup';
    case 'direct':
      return 'Pesan langsung';
    default:
      return 'Ruang obrolan';
  }
}

function lastMessageLabel(room: ChatRoom): string {
  if (!room.last_message_at) return 'Belum ada pesan';
  return relative(room.last_message_at);
}

export default function Chat() {
  const qc = useQueryClient();
  const currentUserId = useAuthStore((s) => s.user?.id ?? null);

  const [activeRoomId, setActiveRoomId] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [live, setLive] = useState(false);
  const [pending, setPending] = useState<ChatMessage[]>([]);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedRef = useRef(false);

  const roomsQuery = useQuery({
    queryKey: ROOMS_KEY,
    queryFn: chatApi.listRooms,
    staleTime: 10_000,
  });

  const rooms = useMemo(() => roomsQuery.data?.items ?? [], [roomsQuery.data]);

  useEffect(() => {
    if (activeRoomId === null && rooms.length > 0) {
      setActiveRoomId(rooms[0].id);
    }
  }, [activeRoomId, rooms]);

  const activeRoom = useMemo(
    () => rooms.find((r) => r.id === activeRoomId) ?? null,
    [rooms, activeRoomId],
  );

  const messagesQuery = useQuery({
    queryKey: ['chat', 'messages', activeRoomId],
    queryFn: () => chatApi.listMessages(activeRoomId as string, { limit: 50, offset: 0 }),
    enabled: Boolean(activeRoomId),
    staleTime: 5_000,
  });

  const messages = useMemo(() => messagesQuery.data?.items ?? [], [messagesQuery.data]);

  const thread = useMemo(() => {
    const known = new Set(messages.map((m) => m.id));
    const extra = pending.filter((m) => !known.has(m.id));
    return [...messages, ...extra].sort(
      (a, b) => +new Date(a.created_at) - +new Date(b.created_at),
    );
  }, [messages, pending]);

  useEffect(() => {
    if (pending.length === 0) return;
    const known = new Set(messages.map((m) => m.id));
    const remaining = pending.filter((m) => !known.has(m.id));
    if (remaining.length !== pending.length) setPending(remaining);
  }, [messages, pending]);

  useEffect(() => {
    if (!activeRoomId) return;
    closedRef.current = false;
    retryRef.current = 0;
    setPending([]);
    setLive(false);

    const connect = () => {
      const ws = new WebSocket(chatApi.wsUrl(activeRoomId));
      wsRef.current = ws;

      ws.onopen = () => {
        retryRef.current = 0;
        setLive(true);
      };
      ws.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data as string) as ChatSocketEvent;
          if (frame.type !== 'message' || !frame.message) return;
          const incoming = frame.message;
          qc.setQueryData<chatApi.ChatMessagePage>(
            ['chat', 'messages', activeRoomId],
            (prev) => {
              if (!prev) return { items: [incoming], total: 1 };
              if (prev.items.some((m) => m.id === incoming.id)) return prev;
              return { items: [...prev.items, incoming], total: prev.total + 1 };
            },
          );
          qc.setQueryData<chatApi.ChatRoomPage>(ROOMS_KEY, (prev) =>
            prev
              ? {
                  ...prev,
                  items: prev.items.map((r) =>
                    r.id === activeRoomId ? { ...r, last_message_at: incoming.created_at } : r,
                  ),
                }
              : prev,
          );
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setLive(false);
        if (closedRef.current) return;
        const delay = Math.min(1000 * 2 ** retryRef.current, 15_000);
        retryRef.current += 1;
        reconnectRef.current = setTimeout(connect, delay);
      };
      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      closedRef.current = true;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      reconnectRef.current = null;
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [activeRoomId, qc]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [thread.length, activeRoomId]);

  const submit = useCallback(async () => {
    const body = draft.trim();
    if (!body || !activeRoomId || sending) return;
    const roomId = activeRoomId;
    const optimistic: ChatMessage = {
      id: 'optimistic-' + Date.now(),
      room_id: roomId,
      sender_id: currentUserId ?? 'me',
      sender_name: null,
      body,
      created_at: new Date().toISOString(),
    };
    setPending((prev) => [...prev, optimistic]);
    setDraft('');
    setSending(true);
    try {
      await chatApi.sendMessage(roomId, body);
    } catch {
      setPending((prev) => prev.filter((m) => m.id !== optimistic.id));
      setDraft(body);
      toast.error('Pesan gagal terkirim', 'Coba lagi sebentar lagi.');
    } finally {
      setSending(false);
    }
  }, [draft, activeRoomId, sending, currentUserId]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void submit();
    }
  };

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Chat"
        title="Obrolan"
        subtitle="Ngobrol dengan grup kegiatan, komunitas, dan pertandinganmu."
        action={
          <Badge tone={live ? 'success' : 'neutral'}>
            {live ? <Wifi className="mr-1 h-3 w-3" /> : <WifiOff className="mr-1 h-3 w-3" />}
            {live ? 'Terhubung' : 'Luring'}
          </Badge>
        }
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <aside className="card flex max-h-[70vh] flex-col overflow-hidden p-0">
          <div className="border-b border-line px-4 py-3">
            <h2 className="text-sm font-semibold text-ink">Ruang</h2>
            <p className="text-xs text-ink-3">Percakapanmu</p>
          </div>
          {roomsQuery.isLoading ? (
            <div className="space-y-2 p-4">
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          ) : roomsQuery.isError ? (
            <div className="p-4">
              <ErrorState title="Gagal memuat ruang" onRetry={() => roomsQuery.refetch()} />
            </div>
          ) : rooms.length === 0 ? (
            <div className="p-4">
              <EmptyState
                icon={<MessageSquare className="h-8 w-8" />}
                title="Belum ada ruang"
                description="Gabung kegiatan atau komunitas dan ruang obrolannya muncul di sini."
              />
            </div>
          ) : (
            <ul className="flex-1 overflow-y-auto p-2" role="listbox" aria-label="Daftar ruang">
              {rooms.map((room) => {
                const isActive = room.id === activeRoomId;
                return (
                  <li key={room.id}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={isActive}
                      onClick={() => setActiveRoomId(room.id)}
                      className={cn(
                        'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors',
                        isActive ? 'bg-action/10' : 'hover:bg-ink/[0.04]',
                      )}
                    >
                      <Avatar name={roomLabel(room)} size={38} />
                      <span className="min-w-0 flex-1">
                        <span className="flex items-center justify-between gap-2">
                          <span className="truncate text-sm font-semibold text-ink">
                            {roomLabel(room)}
                          </span>
                          {room.unread_count > 0 ? (
                            <span className="ml-1 inline-flex min-w-5 items-center justify-center rounded-full bg-action px-1.5 text-2xs font-bold text-action-ink">
                              {room.unread_count > 99 ? '99+' : room.unread_count}
                            </span>
                          ) : null}
                        </span>
                        <span className="block truncate text-xs text-ink-3">
                          {lastMessageLabel(room)}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>

        <section className="card flex max-h-[70vh] min-h-[50vh] flex-col p-0">
          {!activeRoom ? (
            <div className="flex flex-1 items-center justify-center p-6">
              <EmptyState
                icon={<MessageSquare className="h-8 w-8" />}
                title="Pilih ruang"
                description="Pilih salah satu ruang di kiri untuk mulai mengobrol."
              />
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-semibold text-ink">
                    {roomLabel(activeRoom)}
                  </h2>
                  <p className="truncate text-xs text-ink-3">
                    {messagesQuery.data ? messagesQuery.data.total + ' pesan' : 'Memuat...'}
                  </p>
                </div>
              </div>

              <div
                ref={scrollRef}
                className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
                aria-live="polite"
              >
                {messagesQuery.isLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-12 w-2/3" />
                    <Skeleton className="ml-auto h-12 w-1/2" />
                    <Skeleton className="h-12 w-3/5" />
                  </div>
                ) : messagesQuery.isError ? (
                  <ErrorState
                    title="Gagal memuat pesan"
                    onRetry={() => messagesQuery.refetch()}
                  />
                ) : thread.length === 0 ? (
                  <EmptyState
                    icon={<MessageSquare className="h-8 w-8" />}
                    title="Belum ada pesan"
                    description="Mulai percakapan - kirim pesan pertama di ruang ini."
                  />
                ) : (
                  thread.map((m) => {
                    const mine = m.sender_id === currentUserId;
                    return (
                      <div
                        key={m.id}
                        className={cn('flex items-end gap-2', mine ? 'justify-end' : 'justify-start')}
                      >
                        {!mine ? <Avatar name={m.sender_name ?? 'Anggota'} size={32} /> : null}
                        <div className={cn('max-w-[75%]', mine ? 'items-end' : 'items-start')}>
                          {!mine ? (
                            <p className="mb-0.5 px-1 text-2xs font-medium text-ink-3">
                              {m.sender_name ?? 'Anggota'}
                            </p>
                          ) : null}
                          <div
                            className={cn(
                              'whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2 text-sm',
                              mine
                                ? 'bg-action text-ink'
                                : 'bg-surface-muted text-ink ring-1 ring-line',
                            )}
                            title={dateTime(m.created_at)}
                          >
                            {m.body}
                          </div>
                          <p
                            className={cn(
                              'mt-0.5 px-1 text-2xs text-ink-3',
                              mine ? 'text-right' : 'text-left',
                            )}
                          >
                            {clock(m.created_at)}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              <form
                className="flex items-end gap-2 border-t border-line px-4 py-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  void submit();
                }}
              >
                <textarea
                  aria-label="Pesan"
                  placeholder="Tulis pesan..."
                  rows={1}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={onKeyDown}
                  className="max-h-32 min-h-11 flex-1 resize-none rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:ring-2 focus:ring-action"
                />
                <Button
                  type="submit"
                  size="icon"
                  aria-label="Kirim pesan"
                  disabled={draft.trim().length === 0 || sending}
                  loading={sending}
                >
                  {sending ? null : <Send className="h-4 w-4" />}
                </Button>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
