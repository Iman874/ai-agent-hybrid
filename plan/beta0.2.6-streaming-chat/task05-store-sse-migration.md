# Task 5: Store SSE Migration + Fallback Chain

## Deskripsi

Update `chat-store.ts` agar `sendMessage()` menggunakan SSE sebagai primary transport, dengan fallback chain: SSE → WebSocket → HTTP blocking.

## Tujuan Teknis

- `sendMessage()` panggil `sendMessageStream()` (SSE) sebagai default
- Jika SSE gagal → fallback ke WebSocket (existing)
- Jika WS juga gagal → fallback ke HTTP blocking (existing)
- State actions (`appendToken`, `setThinking`, `finalizeStream`, `setError`) TIDAK DIUBAH
- Tambah `_abortController` untuk cancel support

## Scope

**Dikerjakan:**
- Update `sendMessage()` di `app_frontend/src/stores/chat-store.ts`
- Tambah `_abortController` untuk cancel
- Wiring SSE callbacks ke existing state actions

**Tidak dikerjakan:**
- API client (Task 4)
- UI components (tidak perlu diubah)
- WebSocket files (tidak dimodifikasi)

## Langkah Implementasi

### Step 1: Tambah `_abortController` ke interface

File: `app_frontend/src/stores/chat-store.ts`

Tambah ke interface `ChatStore`:

```typescript
interface ChatStore {
  // ... existing fields ...
  _abortController: AbortController | null;
}
```

Dan initial state:

```typescript
_abortController: null,
```

### Step 2: Rewrite `sendMessage()` dengan fallback chain

```typescript
sendMessage: async (text, sessionId) => {
  // 1. Tambah user message ke UI
  const userMsg: Message = {
    id: crypto.randomUUID(),
    role: "user",
    content: text,
    timestamp: Date.now(),
    status: "done",
  };
  set(state => ({ messages: [...state.messages, userMsg] }));

  // 2. Siapkan assistant placeholder
  const assistantId = crypto.randomUUID();
  const assistantMsg: Message = {
    id: assistantId,
    role: "assistant",
    content: "",
    timestamp: Date.now(),
    status: "sending",
  };
  set(state => ({ messages: [...state.messages, assistantMsg] }));

  // 3. PRIMARY: Coba SSE stream
  const abortController = new AbortController();
  set({ _abortController: abortController });

  try {
    const { chatMode, activeModelId } = useModelStore.getState();
    
    await sendMessageStream(
      {
        session_id: sessionId,
        message: text,
        options: {
          chat_mode: chatMode,
          model_preference: activeModelId ?? undefined,
        },
      },
      {
        onStatus: (msg, sid) => {
          // Update session_id jika baru
          if (sid) {
            const currentActiveId = useSessionStore.getState().activeSessionId;
            if (!currentActiveId) {
              useSessionStore.getState().setActiveSession(sid);
              useSessionStore.getState().fetchSessions();
            }
          }
        },
        onThinkingStart: () => get().setThinking(true),
        onThinking: (t) => get().appendThinkingToken(t),
        onThinkingEnd: () => get().setThinking(false),
        onToken: (t) => {
          // Update assistant message status ke streaming
          set(state => ({
            messages: state.messages.map(m =>
              m.id === assistantId && m.status === "sending"
                ? { ...m, status: "streaming" as const }
                : m
            ),
          }));
          get().appendToken(t);
        },
        onDone: (data) => {
          set({ _abortController: null });
          get().finalizeStream(data);
        },
        onError: (msg) => {
          set({ _abortController: null });
          get().setError(assistantId, msg);
        },
      },
      abortController.signal,
    );
    return; // SSE berhasil — selesai
  } catch {
    // SSE gagal — lanjut fallback
    set({ _abortController: null });
  }

  // 4. FALLBACK 1: WebSocket (jika connected)
  const ws = get().wsManager;
  if (ws?.status === "connected") {
    set(state => ({
      stream: { ...state.stream, isStreaming: true },
    }));
    ws.send(text);
    return;
  }

  // 5. FALLBACK 2: HTTP blocking
  try {
    const { chatMode, activeModelId } = useModelStore.getState();
    const response = await apiSendMessage({
      session_id: sessionId,
      message: text,
      options: {
        chat_mode: chatMode,
        model_preference: activeModelId ?? undefined,
      },
    });
    get().finalizeStream(response);
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : "Terjadi kesalahan";
    get().setError(assistantId, errMsg);
  }
},
```

### Step 3: Import `sendMessageStream`

```typescript
import { sendMessage as apiSendMessage, sendMessageStream } from "@/api/chat";
```

### Step 4: Verifikasi existing actions tidak berubah

Pastikan semua method berikut **TIDAK DIMODIFIKASI**:
- `appendToken()` — masih concat ke `stream.partialContent`
- `setThinking()` — masih toggle `stream.isThinking`
- `appendThinkingToken()` — masih concat ke `stream.thinkingText`
- `finalizeStream()` — masih update message + reset stream state
- `setError()` — masih set error pada message tertentu

### Step 5: Verifikasi ChatArea.tsx

Pastikan `ChatArea.tsx` tidak perlu perubahan:
- `stream.partialContent` sudah dirender via `MessageBubble` dengan status `"streaming"`
- `stream.isThinking` sudah dirender via `ThinkingIndicator`
- Kedua komponen ini otomatis bekerja karena data datang via `appendToken()` dan `setThinking()`

## Output yang Diharapkan

```
User ketik pesan → Enter
  ↓
SSE connect ke POST /hybrid/stream
  ↓
onThinkingStart → ThinkingIndicator muncul
onThinking("Analisis...") → thinking text update
onThinkingEnd → ThinkingIndicator hilang
  ↓
onToken("Berdasarkan ") → bubble streaming muncul
onToken("informasi ") → text bertambah
onToken("yang Anda ") → text bertambah
  ↓
onDone({...}) → bubble finalized, session synced
```

## Dependencies

- Task 4: `sendMessageStream()` harus sudah ada di `chat.ts`

## Acceptance Criteria

- [ ] `sendMessage()` panggil SSE duluan (bukan WebSocket)
- [ ] Fallback chain: SSE → WS → HTTP
- [ ] `_abortController` tersedia untuk cancel
- [ ] State actions `appendToken`, `setThinking`, `finalizeStream`, `setError` TIDAK berubah
- [ ] Session sync berfungsi (session_id dari SSE di-set ke session store)
- [ ] `retryMessage()` tetap berfungsi
- [ ] TypeScript build clean
- [ ] UI menampilkan thinking → streaming → done dengan benar

## Estimasi

Medium (2-3 jam)
