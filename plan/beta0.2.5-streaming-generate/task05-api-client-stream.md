# Task 5: API Client — `streamGenerateFromDocument()` + AbortController

## 1. Judul Task
Buat fungsi `streamGenerateFromDocument()` yang consume SSE stream dari backend, dengan support `AbortController` untuk cancel dan error handling lengkap.

## 2. Deskripsi
Fungsi ini mengirim file via `fetch()` ke endpoint streaming, lalu membaca `ReadableStream` dan memanggil callback sesuai tipe event (status, token, done, error). Dilengkapi dengan `AbortSignal` untuk mendukung fitur "Stop Generating".

## 3. Tujuan Teknis
- Fungsi `streamGenerateFromDocument()` di `src/api/generate.ts`
- Parameter: file, context, styleId, callbacks, abortSignal
- Parse SSE format: `data: {...}\n\n`
- Handle: AbortError (user cancel), network error, malformed SSE
- Callbacks: `onStatus`, `onToken`, `onDone`, `onError`

## 4. Scope
### Yang dikerjakan
- Tambah fungsi `streamGenerateFromDocument()` di `src/api/generate.ts`

### Yang tidak dikerjakan
- Tidak mengubah store (task 6)
- Tidak mengubah UI (task 7-8)

## 5. Langkah Implementasi

### Step 1: Tambah import di `src/api/generate.ts`

```typescript
import { API_BASE_URL } from "@/lib/constants";
import type { StreamDoneData } from "@/types/generate";
```

### Step 2: Tambahkan fungsi di akhir file

```typescript
export interface StreamCallbacks {
  onStatus: (msg: string) => void;
  onToken: (text: string) => void;
  onDone: (data: StreamDoneData) => void;
  onError: (msg: string) => void;
}

export async function streamGenerateFromDocument(
  file: File,
  context: string | undefined,
  styleId: string | undefined,
  callbacks: StreamCallbacks,
  abortSignal?: AbortSignal,
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  if (context) formData.append("context", context);
  if (styleId) formData.append("style_id", styleId);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/generate/from-document/stream`, {
      method: "POST",
      body: formData,
      signal: abortSignal,
    });
  } catch (e) {
    // AbortError = user cancelled, bukan error sebenarnya
    if (e instanceof DOMException && e.name === "AbortError") return;
    callbacks.onError(e instanceof Error ? e.message : "Network error");
    return;
  }

  if (!response.ok) {
    callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
    return;
  }

  if (!response.body) {
    callbacks.onError("Response body is null");
    return;
  }

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
          continue; // Skip malformed SSE
        }

        switch (data.type) {
          case "status":
            callbacks.onStatus(data.msg as string);
            break;
          case "token":
            callbacks.onToken(data.t as string);
            break;
          case "done":
            callbacks.onDone(data as unknown as StreamDoneData);
            break;
          case "error":
            callbacks.onError(data.msg as string);
            break;
        }
      }
    }
  } catch (e) {
    // AbortError = user cancelled
    if (e instanceof DOMException && e.name === "AbortError") return;
    // Stream broken tanpa done event
    callbacks.onError("Koneksi terputus saat streaming");
  }
}
```

## 6. Output yang Diharapkan

```typescript
const abort = new AbortController();

await streamGenerateFromDocument(
  myFile,
  "konteks",
  undefined,
  {
    onStatus: (msg) => console.log("Status:", msg),
    onToken: (t) => process.stdout.write(t),
    onDone: (data) => console.log("Done:", data.session_id),
    onError: (msg) => console.error("Error:", msg),
  },
  abort.signal,
);

// Untuk cancel:
abort.abort();
```

## 7. Dependencies
- Task 4 (`StreamDoneData` type)

## 8. Acceptance Criteria
- [ ] Fungsi `streamGenerateFromDocument()` ada di `src/api/generate.ts`
- [ ] Interface `StreamCallbacks` exported
- [ ] Parameter `abortSignal` optional
- [ ] AbortError di-catch dan TIDAK trigger `onError`
- [ ] Network error → `onError("Network error")`
- [ ] HTTP non-200 → `onError("HTTP 500: ...")`
- [ ] Null body → `onError("Response body is null")`
- [ ] Malformed SSE line → skip (tidak crash)
- [ ] Stream broken without done → `onError("Koneksi terputus...")`
- [ ] `npm run build` sukses

## 9. Estimasi
**Medium** (~1 jam)
