# Task 02 — Frontend: API Client `streamGenerateFromChat()`

## 1. Judul Task

Membuat fungsi API client untuk mengkonsumsi SSE endpoint `/generate/chat/stream`.

## 2. Deskripsi

Endpoint backend baru perlu diakses dari React. Task ini menambahkan fungsi `streamGenerateFromChat()` di `src/api/generate.ts` yang identik pola-nya dengan `streamGenerateFromDocument()`, namun mengirim body JSON (`GenerateRequest`) alih-alih `FormData`.

## 3. Tujuan Teknis

- Fungsi baru `streamGenerateFromChat()` di `src/api/generate.ts`.
- Mengirim `POST` request dengan body JSON `{ session_id, mode }`.
- Menggunakan `AbortSignal` untuk cancel support.
- Memakai ulang fungsi `consumeStream()` yang sudah ada (line 107–169 di `generate.ts`).
- Callback interface `StreamCallbacks` yang sudah ada tetap dipakai ulang.

## 4. Scope

### Yang dikerjakan
- Menambahkan 1 exported function baru di `src/api/generate.ts`.

### Yang tidak dikerjakan
- Perubahan store (task terpisah).
- Perubahan UI (task terpisah).
- Perubahan pada `consumeStream()` helper (sudah fungsional).

## 5. Langkah Implementasi

### Step 1: Buka `src/api/generate.ts`

### Step 2: Tambahkan fungsi baru setelah `streamGenerateFromDocument()` (sebelum `retryStream`)

```typescript
/**
 * Streaming TOR generation dari sesi chat.
 * Mengirim JSON body (bukan FormData) ke POST /generate/chat/stream.
 */
export async function streamGenerateFromChat(
  sessionId: string,
  mode: "standard" | "escalation",
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/generate/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        mode: mode,
      }),
      signal: abortSignal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  await consumeStream(response, callbacks);
}
```

### Step 3: Verifikasi

- Import `API_BASE_URL` sudah ada di file (line 2).
- Interface `StreamCallbacks` sudah di-export (line 32).
- Fungsi `consumeStream()` sudah tersedia sebagai private helper (line 107).
- Tidak perlu menambahkan import baru.

## 6. Output yang Diharapkan

Contoh penggunaan dari store:
```typescript
import { streamGenerateFromChat } from "@/api/generate";

await streamGenerateFromChat(
  "session-abc-123",
  "standard",
  {
    onStatus: (msg) => console.log("Status:", msg),
    onToken: (t) => console.log("Token:", t),
    onDone: (data) => console.log("Done:", data),
    onError: (msg) => console.error("Error:", msg),
  },
  abortController.signal,
);
```

## 7. Dependencies

- **Task 01** harus selesai (endpoint `POST /generate/chat/stream` harus tersedia di backend).

## 8. Acceptance Criteria

- [ ] Fungsi `streamGenerateFromChat()` ter-export dari `src/api/generate.ts`.
- [ ] Mengirim request `POST` dengan header `Content-Type: application/json`.
- [ ] Body berisi `{ session_id: string, mode: string }`.
- [ ] Mendukung `AbortSignal` untuk cancel.
- [ ] `AbortError` di-handle silent (tidak memanggil `onError`).
- [ ] Mereuse `consumeStream()` internal untuk parsing SSE.
- [ ] `npm run build` → zero TypeScript errors.

## 9. Estimasi

**Low** — ~30 menit kerja (copy-adjust dari `streamGenerateFromDocument`, ganti FormData → JSON).
