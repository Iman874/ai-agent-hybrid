# Task 20: Frontend API Client `sendMessageStream()`

## Deskripsi

Menambahkan SSE consumer function `sendMessageStream()` di frontend API client, menggunakan pola `consumeStream` yang sudah teruji di `generate.ts`.

## Tujuan Teknis

- Fungsi `sendMessageStream()` di `app_frontend/src/api/chat.ts`
- Menggunakan `fetch` + SSE parsing (bukan WebSocket)
- Callbacks: `onStatus`, `onThinking`, `onToken`, `onDone`, `onError`
- Support `AbortSignal` untuk cancel

## Scope

**Dikerjakan:**
- Tambah `sendMessageStream()` di `api/chat.ts`
- Tambah tipe `ChatStreamCallbacks` 
- Reuse atau copy pola `consumeStream` dari `generate.ts`

**Tidak dikerjakan:**
- Store integration (Task 21)
- UI components (tidak perlu diubah)

## Langkah Implementasi

### Step 1: Definisikan callback interface

File: `app_frontend/src/api/chat.ts`

```typescript
export interface ChatStreamCallbacks {
  onStatus: (msg: string, sessionId?: string) => void;
  onThinkingStart: () => void;
  onThinking: (text: string) => void;
  onThinkingEnd: () => void;
  onToken: (text: string) => void;
  onDone: (data: HybridResponse) => void;
  onError: (msg: string) => void;
}
```

### Step 2: Implementasi `sendMessageStream()`

```typescript
import { API_BASE_URL } from "@/lib/constants";
import type { HybridRequest, HybridResponse } from "@/types/api";

export async function sendMessageStream(
  req: HybridRequest,
  callbacks: ChatStreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/hybrid/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: abortSignal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  if (!response.ok) {
    try {
      const errBody = await response.json();
      callbacks.onError(errBody?.detail || `HTTP ${response.status}: ${response.statusText}`);
    } catch {
      callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
    }
    return;
  }

  if (!response.body) {
    callbacks.onError("Response body is null");
    return;
  }

  // SSE consumer — pola identik dengan consumeStream di generate.ts
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        let data: Record<string, unknown>;
        try {
          data = JSON.parse(line.slice(6));
        } catch {
          continue;
        }

        switch (data.type) {
          case "status":
            callbacks.onStatus(
              data.msg as string,
              data.session_id as string | undefined,
            );
            break;
          case "thinking_start":
            callbacks.onThinkingStart();
            break;
          case "thinking":
            callbacks.onThinking(data.t as string);
            break;
          case "thinking_end":
            callbacks.onThinkingEnd();
            break;
          case "token":
            callbacks.onToken(data.t as string);
            break;
          case "done":
            callbacks.onDone(data as unknown as HybridResponse);
            break;
          case "error":
            callbacks.onError(data.msg as string);
            break;
        }
      }
    }
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError("Koneksi terputus saat streaming");
  }
}
```

### Step 3: Pastikan existing `sendMessage()` tetap ada

```typescript
// Existing — JANGAN DIHAPUS (dipakai sebagai HTTP fallback)
export async function sendMessage(req: HybridRequest): Promise<HybridResponse> {
  return apiPost<HybridResponse>("/hybrid", req);
}
```

## Output yang Diharapkan

File `chat.ts` memiliki:
1. `sendMessage()` — HTTP blocking (existing, tetap)
2. `sendMessageStream()` — SSE streaming (baru)

## Dependencies

- Task 19: SSE endpoint `POST /hybrid/stream` harus sudah ada

## Acceptance Criteria

- [ ] `sendMessageStream()` ditambahkan ke `chat.ts`
- [ ] Menggunakan pola SSE consumer (bukan WebSocket)
- [ ] Support semua event types: `status`, `thinking_start`, `thinking`, `thinking_end`, `token`, `done`, `error`
- [ ] Support `AbortSignal` untuk cancel
- [ ] Error response dari backend ditangkap (detail message, bukan generic)
- [ ] Existing `sendMessage()` tidak dihapus
- [ ] TypeScript build clean

## Estimasi

Low (1 jam)
