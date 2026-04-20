# Task 6: Store — Streaming State + Cancel + Timeout

## 1. Judul Task
Extend `generate-store.ts` dengan streaming state, cancel support, dan safety timeout.

## 2. Deskripsi
Store Zustand perlu state baru untuk mengelola streaming: teks yang sedang di-stream, status message, error, cancel via AbortController, dan safety timeout 120 detik. State `streamingContent` TIDAK pernah di-reset saat error/cancel (partial preservation).

## 3. Tujuan Teknis
- State baru: `streamingContent`, `streamingStatus`, `isStreaming`, `streamError`, `streamSessionId`, `streamMetadata`
- Actions: `generateFromDocStream()`, `cancelStream()`, `clearStreamState()`
- Internal: `_abortController` reference
- Safety timeout 120 detik: auto-abort jika stream melebihi batas
- `isStreaming` strict lifecycle: true HANYA saat stream aktif

## 4. Scope
### Yang dikerjakan
- Modifikasi `src/stores/generate-store.ts`

### Yang tidak dikerjakan
- Tidak mengubah UI (task 7-8)

## 5. Langkah Implementasi

### Step 1: Tambah imports

```typescript
import { streamGenerateFromDocument } from "@/api/generate";
import type { StreamDoneData } from "@/types/generate";
```

### Step 2: Extend interface GenerateStore

```typescript
interface GenerateStore {
  // --- Existing ---
  history: DocGenListItem[];
  isLoadingHistory: boolean;
  fetchHistory: () => Promise<void>;
  activeResult: DocGenDetail | null;
  isLoadingResult: boolean;
  viewResult: (id: string) => Promise<void>;
  clearActiveResult: () => void;
  lastGenerateResponse: GenerateResponse | null;
  isGenerating: boolean;
  generateFromDoc: (file: File, context?: string, styleId?: string) => Promise<void>;
  clearLastResponse: () => void;
  deleteGeneration: (id: string) => Promise<void>;

  // --- Streaming (NEW) ---
  streamingContent: string;
  streamingStatus: string;
  isStreaming: boolean;
  streamError: string | null;
  streamSessionId: string | null;
  streamMetadata: StreamDoneData["metadata"] | null;
  
  generateFromDocStream: (file: File, context?: string, styleId?: string) => Promise<void>;
  cancelStream: () => void;
  clearStreamState: () => void;

  // Internal (non-reactive)
  _abortController: AbortController | null;
}
```

### Step 3: Tambah initial values di `create<GenerateStore>()`

```typescript
// Streaming initial state
streamingContent: "",
streamingStatus: "",
isStreaming: false,
streamError: null,
streamSessionId: null,
streamMetadata: null,
_abortController: null,
```

### Step 4: Implementasi actions

```typescript
generateFromDocStream: async (file, context, styleId) => {
  const abortController = new AbortController();
  set({
    isStreaming: true,
    streamingContent: "",
    streamingStatus: "",
    streamError: null,
    streamSessionId: null,
    streamMetadata: null,
    _abortController: abortController,
    lastGenerateResponse: null,
  });

  // Safety timeout: 120 detik max
  const safetyTimeout = setTimeout(() => {
    const state = get();
    if (state.isStreaming) {
      abortController.abort();
      set({
        isStreaming: false,
        streamError: "Timeout: generate melebihi batas waktu (120 detik)",
      });
    }
  }, 120_000);

  try {
    await streamGenerateFromDocument(file, context, styleId, {
      onStatus: (msg) => set({ streamingStatus: msg }),
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
      onError: (msg) => {
        clearTimeout(safetyTimeout);
        // PARTIAL PRESERVATION: streamingContent TIDAK di-reset
        set({
          isStreaming: false,
          streamError: msg,
          _abortController: null,
        });
        get().fetchHistory();
      },
    }, abortController.signal);
  } catch {
    clearTimeout(safetyTimeout);
    set({ isStreaming: false, _abortController: null });
  }
},

cancelStream: () => {
  const ctrl = get()._abortController;
  if (ctrl) ctrl.abort();
  // PARTIAL PRESERVATION: content tetap, error message set
  set({
    isStreaming: false,
    streamError: "Dibatalkan oleh user",
    _abortController: null,
  });
  get().fetchHistory();
},

clearStreamState: () => set({
  streamingContent: "",
  streamingStatus: "",
  streamError: null,
  streamSessionId: null,
  streamMetadata: null,
  isStreaming: false,
  _abortController: null,
}),
```

## 6. Output yang Diharapkan

```typescript
const store = useGenerateStore.getState();

// Start streaming
await store.generateFromDocStream(myFile, "konteks");
// → isStreaming = true
// → streamingContent accumulates: "# TOR..." 
// → onDone → isStreaming = false, streamSessionId = "doc-abc"

// Cancel
store.cancelStream();
// → isStreaming = false
// → streamError = "Dibatalkan oleh user"
// → streamingContent TETAP ada (partial)

// Reset
store.clearStreamState();
// → semua streaming state di-reset ke initial
```

## 7. Dependencies
- Task 5 (API client `streamGenerateFromDocument`)

## 8. Acceptance Criteria
- [ ] State `isStreaming` strict: true saat stream aktif, false saat done/error/cancel/timeout
- [ ] `streamingContent` accumulates dari `onToken`, TIDAK pernah reset saat error/cancel
- [ ] `cancelStream()` memanggil `abortController.abort()`
- [ ] Safety timeout 120s: auto-abort dan set error
- [ ] `clearStreamState()` resets semua streaming state
- [ ] `onDone` triggers `fetchHistory()`
- [ ] `onError` triggers `fetchHistory()`
- [ ] Existing store functionality (history, viewResult, etc) TIDAK berubah
- [ ] `npm run build` sukses

## 9. Estimasi
**Medium** (~1 jam)
