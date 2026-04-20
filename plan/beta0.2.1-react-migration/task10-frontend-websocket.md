# Task 10: Frontend WebSocket — Manager + Hook + Store Integration

## 1. Judul Task

Implementasi WebSocket manager, React hook, dan integrasi ke chat store

## 2. Deskripsi

Membuat `WebSocketManager` class yang mengelola koneksi WS, `useWebSocket` hook untuk lifecycle management, dan menghubungkannya ke `chat-store` agar token streaming langsung update UI.

## 3. Tujuan Teknis

- `ws/socket.ts` — WebSocketManager class (connect, send, reconnect, heartbeat)
- `ws/fallback.ts` — HTTP fallback jika WS gagal
- `hooks/useWebSocket.ts` — hook yang bridge WS → store
- Update `chat-store.ts` — `sendMessage` cek WS dulu, fallback HTTP

## 4. Scope

**Yang dikerjakan:**
- `src/ws/socket.ts`
- `src/ws/types.ts`
- `src/ws/fallback.ts`
- `src/hooks/useWebSocket.ts`
- Update `src/stores/chat-store.ts` — integrate WS

**Yang tidak dikerjakan:**
- Backend WS (task 09 — sudah selesai)
- Streaming UI components (task 11)

## 5. Langkah Implementasi

### 5.1 `src/ws/types.ts`

```typescript
export type WSStatus = "connecting" | "connected" | "disconnected" | "error";

export interface WSCallbacks {
  onToken: (token: string) => void;
  onThinkingStart: () => void;
  onThinkingToken: (token: string) => void;
  onThinkingEnd: () => void;
  onDone: (data: any) => void;
  onError: (error: string) => void;
  onStatusChange: (status: WSStatus) => void;
}
```

### 5.2 `src/ws/socket.ts`

Full WebSocketManager class as described in plan design section 7.1:
- Exponential reconnect (1s → 2s → 4s → max 30s, max 5 attempts)
- Heartbeat every 30s
- All callbacks wired to store actions

### 5.3 `src/ws/fallback.ts`

HTTP fallback function that simulates streaming by splitting words.

### 5.4 `src/hooks/useWebSocket.ts`

```typescript
import { useEffect, useRef } from "react";
import { WebSocketManager } from "@/ws/socket";
import { useChatStore } from "@/stores/chat-store";
import { useSessionStore } from "@/stores/session-store";

export function useWebSocket() {
  const wsRef = useRef<WebSocketManager | null>(null);
  const activeSessionId = useSessionStore(s => s.activeSessionId);
  const { appendToken, setThinking, appendThinkingToken, finalizeStream, setError } = useChatStore();

  useEffect(() => {
    const ws = new WebSocketManager("");
    ws.onToken = appendToken;
    ws.onThinkingStart = () => setThinking(true);
    ws.onThinkingToken = appendThinkingToken;
    ws.onThinkingEnd = () => setThinking(false);
    ws.onDone = finalizeStream;
    ws.onError = (err) => {
      // Set error on last assistant message
      const messages = useChatStore.getState().messages;
      const last = [...messages].reverse().find(m => m.role === "assistant");
      if (last) setError(last.id, err);
    };
    ws.connect(activeSessionId ?? undefined);
    wsRef.current = ws;

    return () => ws.disconnect();
  }, [activeSessionId]);

  return wsRef;
}
```

### 5.5 Update `chat-store.ts` sendMessage

```typescript
// Add WS reference to store
wsManager: null as WebSocketManager | null,
setWSManager: (ws) => set({ wsManager: ws }),

sendMessage: async (text, sessionId) => {
  // Add user message
  // ...

  const ws = get().wsManager;
  if (ws?.status === "connected") {
    // Use WebSocket streaming
    set(state => ({
      stream: { ...state.stream, isStreaming: true },
    }));
    ws.send(text);
  } else {
    // HTTP fallback
    // ... existing POST logic
  }
},
```

## 6. Output yang Diharapkan

- Kirim pesan → WS connected → token-by-token response
- WS disconnect → auto-reconnect (exponential backoff)
- Max 5 attempts → fallback ke HTTP POST

## 7. Dependencies

- Task 04 (chat store)
- Task 09 (backend WS endpoint)

## 8. Acceptance Criteria

- [ ] WS connects on app mount
- [ ] Tokens stream to chat-store
- [ ] Thinking state triggers properly
- [ ] Reconnect on disconnect (max 5 attempts)
- [ ] Heartbeat ping/pong setiap 30s
- [ ] Fallback ke HTTP jika WS gagal total

## 9. Estimasi

High (2-3 jam)
