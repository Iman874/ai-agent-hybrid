# Task 03 — Frontend: Generate Store Action `generateFromChatStream()`

## 1. Judul Task

Menambahkan action `generateFromChatStream()` di `generate-store.ts` untuk memulai streaming TOR dari sesi chat.

## 2. Deskripsi

Store Zustand `generate-store.ts` sudah punya `generateFromDocStream()` untuk streaming dari file upload. Task ini menambahkan satu action baru `generateFromChatStream()` yang cara kerjanya identik, tapi memanggil `streamGenerateFromChat()` dengan parameter `sessionId` dan `mode`, tanpa `file`.

## 3. Tujuan Teknis

- Menambahkan method baru `generateFromChatStream` di interface `GenerateStore`.
- Implementasi me-reuse pola yang sama dengan `generateFromDocStream()` (safety timeout, abort controller, callback wiring, partial preservation).
- Action ini akan dipanggil dari `chat-store.ts` saat chat menerima status `READY_TO_GENERATE`.

## 4. Scope

### Yang dikerjakan
- Tambahkan `generateFromChatStream` ke interface `GenerateStore` (definisi type).
- Implementasikan method pada body Zustand store.

### Yang tidak dikerjakan
- Memanggil action ini dari `chat-store` (task terpisah).
- Perubahan UI (task terpisah).

## 5. Langkah Implementasi

### Step 1: Tambahkan import baru di `src/stores/generate-store.ts`

Di line 3, tambahkan `streamGenerateFromChat`:
```typescript
import { streamGenerateFromDocument, savePartialContent, retryStream, continueStream, streamGenerateFromChat } from "@/api/generate";
```

### Step 2: Tambahkan method ke interface `GenerateStore`

Di dalam blok `interface GenerateStore` (setelah `generateFromDocStream`, sekitar line 36):
```typescript
  generateFromChatStream: (sessionId: string, mode: "standard" | "escalation") => Promise<void>;
```

### Step 3: Implementasikan method di body store

Tambahkan setelah implementasi `generateFromDocStream` (sekitar line 180, sebelum `retryGeneration`):

```typescript
  generateFromChatStream: async (sessionId, mode) => {
    const abortController = new AbortController();
    set({
      isStreaming: true,
      streamingContent: "",
      streamingStatus: "",
      streamError: null,
      streamSessionId: sessionId, // Sudah tahu session_id dari chat
      streamMetadata: null,
      _abortController: abortController,
      _sourceGenId: null,
      lastGenerateResponse: null,
    });

    // Safety timeout: 300 detik (5 menit) max
    const safetyTimeout = setTimeout(() => {
      const state = get();
      if (state.isStreaming) {
        abortController.abort();
        set({
          isStreaming: false,
          streamError: "Timeout: generate melebihi batas waktu (300 detik)",
        });
      }
    }, 300_000);

    try {
      await streamGenerateFromChat(sessionId, mode, {
        onStatus: (msg, sid) => {
          const updates: Partial<GenerateStore> = { streamingStatus: msg };
          if (sid) updates.streamSessionId = sid;
          set(updates);
        },
        onToken: (t) => set(s => ({ streamingContent: s.streamingContent + t })),
        onDone: (data) => {
          clearTimeout(safetyTimeout);
          set({
            isStreaming: false,
            streamSessionId: data.session_id,
            streamMetadata: data.metadata,
            streamingStatus: "",
            _abortController: null,
          });
          get().fetchHistory();
        },
        onError: async (msg) => {
          clearTimeout(safetyTimeout);
          const currentSessionId = get().streamSessionId;
          const currentContent = get().streamingContent;
          // PARTIAL PRESERVATION: streamingContent TIDAK di-reset
          set({
            isStreaming: false,
            streamError: msg,
            _abortController: null,
          });
          // Simpan partial content jika ada
          if (currentSessionId && currentContent) {
            await savePartialContent(currentSessionId, currentContent, msg);
          }
          get().fetchHistory();
        },
      }, abortController.signal);
    } catch {
      clearTimeout(safetyTimeout);
      set({ isStreaming: false, _abortController: null });
    }
  },
```

## 6. Output yang Diharapkan

Setelah task ini selesai, fungsi berikut dapat dipanggil dari mana saja:

```typescript
import { useGenerateStore } from "@/stores/generate-store";

// Trigger streaming TOR dari sesi chat
useGenerateStore.getState().generateFromChatStream("session-abc", "standard");
```

State yang berubah selama proses:
1. `isStreaming: true` → token mulai masuk
2. `streamingContent` bertumbuh per token
3. `isStreaming: false` + `streamSessionId` terisi → done
4. Auto-transition ke `GenerateResult` view (ditangani oleh `GenerateContainer.tsx` yang sudah ada via `useEffect`)

## 7. Dependencies

- **Task 02** harus selesai (`streamGenerateFromChat()` harus tersedia di `src/api/generate.ts`).

## 8. Acceptance Criteria

- [ ] Method `generateFromChatStream(sessionId, mode)` terdaftar di interface `GenerateStore`.
- [ ] Implementasi menggunakan `AbortController` + safety timeout 300 detik.
- [ ] `streamSessionId` langsung di-set ke `sessionId` parameter (tidak menunggu callback).
- [ ] Callback `onToken` meng-append ke `streamingContent`.
- [ ] Callback `onDone` men-set `isStreaming: false` dan memanggil `fetchHistory()`.
- [ ] Callback `onError` men-set `streamError`, mem-preserve `streamingContent`, dan memanggil `savePartialContent()`.
- [ ] `cancelStream()` yang sudah ada tetap berfungsi untuk membatalkan streaming ini.
- [ ] `clearStreamState()` yang sudah ada tetap berfungsi untuk mereset state.
- [ ] `npm run build` → zero TypeScript errors.

## 9. Estimasi

**Low** — ~45 menit kerja (copy-adjust dari `generateFromDocStream`, ganti parameter).
