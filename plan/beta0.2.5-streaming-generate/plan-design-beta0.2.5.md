# Beta 0.2.5 — Streaming Generate TOR dari Dokumen

## 1. Ringkasan

Mengganti pengalaman "loading spinner → hasil lengkap" dengan **streaming kata per kata** saat generate TOR dari dokumen. User akan melihat teks TOR muncul secara progresif di layar — persis seperti pengalaman ChatGPT/Gemini saat menjawab pertanyaan.

**Teknologi**: Server-Sent Events (SSE) + Gemini `generate_content(stream=True)`.

**Reliability**: Streaming dilengkapi dengan disconnect detection, cancel/stop, timeout handling, throttled rendering, dan partial result preservation — siap kondisi production nyata.

---

## 2. Analisis Arsitektur Saat Ini

### Alur Sekarang (Blocking)

```
Frontend                          Backend
────────                          ───────
UploadForm                        POST /generate/from-document
  ↓ POST (file + context)          ↓ Parse file
  ↓                                ↓ Build prompt
  ↓ [LOADING SPINNER ⏳]           ↓ gemini.generate(prompt) ← BLOCKING 15-60 detik
  ↓                                ↓ post_processor.process()
  ↓                                ↓ Persist to DB
  ← JSON response (full TOR)      ← Return GenerateResponse
GenerateResult renders
```

**Masalah**: User staring at a spinner for 15-60 seconds. No feedback, no progress indication.

### Alur Target (Streaming + Reliability)

```
Frontend                              Backend
────────                              ───────
UploadForm                            POST /generate/from-document/stream
  ↓ POST (file + context)              ↓ Parse file (1-2s)
  ↓ AbortController ready              ↓ Build prompt
  ← SSE: {"type":"status","msg":...}   ← "Memproses dokumen..."
  ← SSE: {"type":"status","msg":...}   ← "Memanggil AI..."
  ← SSE: {"type":"token","t":"# "}     ← Gemini stream chunk 1
  ← SSE: {"type":"token","t":"TOR "}   ← Gemini stream chunk 2
  ← SSE: {"type":"token","t":"Keg"}    ← Gemini stream chunk 3
  ← ...                                ← ... (ratusan chunks)
  ← ...                                ← ↕ Setiap loop: cek disconnect
  ← SSE: {"type":"done","data":{...}}  ← Final: post-process + persist DB
  GenerateResult shows complete TOR
                                       
  [Stop Generating] button             ← AbortController.abort()
    → reader cancel                    ← request.is_disconnected() → break
    → show partial result              ← skip post-process, persist partial
```

---

## 3. Kenapa SSE (Bukan WebSocket)?

| Kriteria | SSE | WebSocket |
|----------|-----|-----------|
| Directionality | Server → Client (cocok) | Bidirectional (overkill) |
| Complexity | Minimal, standard HTTP | Handshake, connection mgmt |
| File upload | `multipart/form-data` langsung | Harus encode binary to WS |
| Error handling | HTTP status codes | Custom error frames |
| Auto-reconnect | Built-in di browser | Manual |
| Cancel support | `AbortController` native | Custom close frame |

> [!TIP]
> SSE lebih sederhana, dan kita hanya butuh one-way streaming (server → client). File upload tetap bisa pakai `fetch()` biasa — kita hanya ganti response format dari JSON ke SSE stream.

---

## 4. Backend: Perubahan

### 4.1 SSE Utility: `app/utils/sse.py`

```python
import json

def sse_event(event_type: str, data: dict | None = None) -> str:
    """Format SSE event. Semua event WAJIB punya 'type' field."""
    payload = {"type": event_type}
    if data:
        payload.update(data)
    return f"data: {json.dumps(payload)}\n\n"
```

### 4.2 GeminiProvider: Tambah `generate_stream()`

Menambah method baru di `gemini_provider.py` dengan **timeout protection**:

```python
async def generate_stream(
    self, prompt: str, timeout: float | None = None
) -> AsyncGenerator[str, None]:
    """Stream generate content — yield text chunks.
    
    Args:
        prompt: The prompt to generate from.
        timeout: Max seconds for entire stream. Defaults to self.timeout.
    
    Raises:
        GeminiTimeoutError: If stream exceeds timeout.
    """
    effective_timeout = timeout or self.timeout
    start = time.monotonic()
    
    try:
        # generate_content with stream=True returns iterable
        response = await asyncio.to_thread(
            self.model.generate_content, prompt, stream=True
        )
    except Exception as e:
        error_str = str(e)
        if "API_KEY" in error_str.upper() or "INVALID" in error_str.upper():
            raise GeminiAPIError(details=f"API key mungkin tidak valid: {error_str[:200]}")
        raise GeminiAPIError(details=error_str[:200])
    
    # Iterate chunks — each chunk has .text
    # Wrapping sync iterator into async yields via to_thread per chunk
    for chunk in response:
        # Timeout check
        elapsed = time.monotonic() - start
        if elapsed > effective_timeout:
            raise GeminiTimeoutError(effective_timeout)
        
        if chunk.text:
            yield chunk.text
```

> [!IMPORTANT]
> `generate_content(prompt, stream=True)` mengembalikan **sync iterable**. Karena Gemini SDK saat ini synchronous, kita perlu wrap call awal di `to_thread`. Iterasi chunk bisa tetap sync karena data sudah ada di buffer lokal setelah network call.

### 4.3 Endpoint Baru: `POST /generate/from-document/stream`

Endpoint dengan **disconnect detection** dan **error standardization**:

```python
from fastapi.responses import StreamingResponse
from app.utils.sse import sse_event

@router.post("/generate/from-document/stream")
async def generate_from_document_stream(
    request: Request,
    file: UploadFile = File(...),
    context: str = Form(""),
    style_id: str | None = Form(None),
):
    # Step 1-3: Read file, get style, persist 'processing' (SAMA dengan blocking)
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    style_manager = request.app.state.style_manager
    doc_gen_repo = request.app.state.doc_gen_repo

    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"
    session_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Resolve style
    active_style = ...  # (sama seperti blocking endpoint)

    # Persist processing
    await doc_gen_repo.create(
        gen_id=session_id, filename=filename, file_size=len(file_bytes),
        context=context, style_id=..., style_name=...,
    )

    async def event_stream():
        full_text = ""
        cancelled = False

        try:
            # === DISCONNECT CHECK MACRO ===
            # Setiap fase wajib cek: apakah client masih terhubung?
            
            # Phase 1: Parse
            if await request.is_disconnected():
                cancelled = True; return
            yield sse_event("status", {"msg": "Memproses dokumen..."})
            document_text = await DocumentParser.parse(file_bytes, filename)

            # Phase 2: RAG + Prompt
            if await request.is_disconnected():
                cancelled = True; return
            yield sse_event("status", {"msg": "Menyusun prompt..."})
            rag_examples = ...  # (optional RAG)
            format_spec = active_style.to_prompt_spec()
            prompt = GeminiPromptBuilder.build_from_document(
                document_text=document_text, user_context=context,
                rag_examples=rag_examples, format_spec=format_spec,
            )

            # Phase 3: Stream Gemini
            if await request.is_disconnected():
                cancelled = True; return
            yield sse_event("status", {"msg": "Menghasilkan TOR..."})

            async for chunk in gemini.generate_stream(prompt):
                # Disconnect check setiap chunk
                if await request.is_disconnected():
                    cancelled = True
                    break

                full_text += chunk
                yield sse_event("token", {"t": chunk})

            # Jika cancelled mid-stream, JANGAN post-process
            if cancelled:
                return

            # Phase 4: Post-process (hanya setelah stream selesai LENGKAP)
            processed = post_processor.process(full_text, style=active_style)

            # Phase 5: Persist completed
            tor_metadata = {
                "generated_by": gemini.model_name,
                "mode": "standard",
                "word_count": processed.word_count,
                "has_assumptions": processed.has_assumptions,
            }
            await doc_gen_repo.update_completed(
                session_id,
                tor_content=processed.content,
                metadata_json=json.dumps(tor_metadata),
            )

            # Store di cache untuk export
            tor_doc = TORDocument(
                content=processed.content,
                metadata=TORMetadata(**tor_metadata, generation_time_ms=0,
                    prompt_tokens=0, completion_tokens=0),
            )
            tor_cache = request.app.state.tor_cache
            await tor_cache.store(session_id, tor_doc)

            # Phase 6: Done event
            yield sse_event("done", {
                "session_id": session_id,
                "metadata": tor_metadata,
            })

        except GeminiTimeoutError as e:
            # WAJIB: kirim error event, bukan silent fail
            await doc_gen_repo.update_failed(session_id, f"Timeout: {e}")
            yield sse_event("error", {"msg": f"Timeout saat generate ({e})"})

        except Exception as e:
            # WAJIB: semua exception → error SSE event
            await doc_gen_repo.update_failed(session_id, str(e)[:500])
            yield sse_event("error", {"msg": str(e)[:300]})

        finally:
            # Jika cancelled mid-stream dan ada partial text, persist sebagai failed
            if cancelled and full_text:
                await doc_gen_repo.update_failed(
                    session_id,
                    f"Dibatalkan oleh user. Partial: {len(full_text)} chars"
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Prevent nginx buffering
        },
    )
```

### 4.4 Endpoint Lama Dipertahankan

`POST /generate/from-document` (blocking) **tetap ada** sebagai fallback.

---

## 5. Frontend: Perubahan

### 5.1 Types: `StreamDoneData`

```typescript
// src/types/generate.ts — tambah:

export interface StreamDoneData {
  session_id: string;
  metadata: {
    generated_by: string;
    mode: string;
    word_count: number;
    has_assumptions: boolean;
  };
}
```

### 5.2 API Client: `streamGenerateFromDocument()`

Dengan **AbortController**, **error handling**, dan **stream close protection**:

```typescript
export async function streamGenerateFromDocument(
  file: File,
  context: string | undefined,
  styleId: string | undefined,
  callbacks: {
    onStatus: (msg: string) => void;
    onToken: (text: string) => void;
    onDone: (data: StreamDoneData) => void;
    onError: (msg: string) => void;
  },
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
      signal: abortSignal,  // ← AbortController support
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
          case "status": callbacks.onStatus(data.msg as string); break;
          case "token":  callbacks.onToken(data.t as string); break;
          case "done":   callbacks.onDone(data as unknown as StreamDoneData); break;
          case "error":  callbacks.onError(data.msg as string); break;
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

### 5.3 Generate Store: Streaming State + Reliability

State baru di `generate-store.ts` dengan **cancel**, **timeout warning**, dan **partial preservation**:

```typescript
interface GenerateStore {
  // ... existing (history, activeResult, lastGenerateResponse) ...

  // === Streaming State ===
  streamingContent: string;        // Teks TOR yang sedang di-stream
  streamingStatus: string;         // Status: "Memproses dokumen..."
  isStreaming: boolean;            // True saat streaming aktif
  streamError: string | null;      // Error message jika gagal
  streamSessionId: string | null;  // Session ID dari done event
  streamMetadata: StreamDoneData["metadata"] | null;

  // === Streaming Actions ===
  generateFromDocStream: (file: File, context?: string, styleId?: string) => Promise<void>;
  cancelStream: () => void;         // ← CANCEL SUPPORT
  clearStreamState: () => void;     // Reset semua streaming state

  // === Internal (dipanggil dari callback) ===
  _abortController: AbortController | null;
}
```

**Implementasi kunci**:

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

  // Timeout safety: jika 120 detik tanpa done, paksa error
  const safetyTimeout = setTimeout(() => {
    const state = get();
    if (state.isStreaming) {
      abortController.abort();
      set({
        isStreaming: false,
        streamError: "Timeout: generate melebihi batas waktu",
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
        });
        // Refresh history
        get().fetchHistory();
      },
      onError: (msg) => {
        clearTimeout(safetyTimeout);
        // PARTIAL PRESERVATION: streamingContent TIDAK di-reset
        set({
          isStreaming: false,
          streamError: msg,
        });
        get().fetchHistory();
      },
    }, abortController.signal);
  } catch {
    clearTimeout(safetyTimeout);
    set({ isStreaming: false });
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

> [!IMPORTANT]
> **State consistency rules**:
> - `isStreaming` = `true` HANYA saat stream aktif. Menjadi `false` pada: done, error, cancel, timeout.
> - `streamingStatus` selalu di-update dari event `status`.
> - `streamingContent` TIDAK pernah di-reset saat error/cancel — ini partial preservation.

### 5.4 UI: View States

`GenerateContainer.tsx` mendapat view state ke-4 dan ke-5:

```
┌────────────────────────────────────────────┐
│ View States:                               │
│                                            │
│  1. idle       → UploadForm + History      │
│  2. streaming  → StreamingResult (LIVE)    │
│  3. partial    → StreamingResult (ERROR)   │
│  4. viewing    → GenerateResult            │
│  5. loading    → Spinner (detail fetch)    │
└────────────────────────────────────────────┘
```

### 5.5 Komponen Baru: `StreamingResult.tsx`

Menampilkan TOR yang sedang di-stream secara live:

```
┌─────────────────────────────────────────────┐
│  ⏳ Menghasilkan TOR...     [Stop Generating]│  ← Cancel button
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ # TOR Kegiatan Pelatihan A...         │  │
│  │                                        │  │
│  │ ## 1. Latar Belakang                   │  │
│  │ Berdasarkan hasil evaluasi...          │  │
│  │ █  ← kursor berkedip                  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Streaming... 847 chars | 12.3s              │
└──────────────────────────────────────────────┘
```

**Setelah Error / Cancel (Partial Result):**
```
┌─────────────────────────────────────────────┐
│  ⚠ Hasil belum lengkap         [← Kembali] │
│  Dibatalkan oleh user                       │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ # TOR Kegiatan Pelatihan A...         │  │
│  │ ## 1. Latar Belakang                   │  │
│  │ Berdasarkan hasil evalua               │  │  ← terpotong
│  └────────────────────────────────────────┘  │
│                                              │
│  [Coba Lagi]                                 │
└──────────────────────────────────────────────┘
```

**Fitur WAJIB**:
1. **Throttled Rendering** — Markdown di-render max 10 FPS (throttle 100ms) menggunakan `requestAnimationFrame` + timer. Raw text terus di-accumulate, render di-batch.
2. **Kursor berkedip** — CSS `@keyframes blink` di akhir teks saat `isStreaming=true`
3. **Counter** — Jumlah chars + elapsed time
4. **Auto-scroll** — Scroll ke bawah saat teks bertambah (via `scrollIntoView`)
5. **Status bar** — Menampilkan `streamingStatus` ("Memproses dokumen...", dll)
6. **Stop button** — Memanggil `cancelStream()` dari store
7. **Partial result** — Jika error/cancel, teks tetap tampil dengan peringatan
8. **Retry button** — Muncul saat error, memanggil ulang `generateFromDocStream`
9. **Transisi otomatis** — Setelah `done` event, transisi ke `GenerateResult` view setelah 500ms delay

**Throttled Rendering Implementation**:
```typescript
// Di dalam StreamingResult.tsx
const [renderedContent, setRenderedContent] = useState("");
const streamingContent = useGenerateStore(s => s.streamingContent);

useEffect(() => {
  // Throttle: update rendered content max setiap 100ms
  const timer = setTimeout(() => {
    setRenderedContent(streamingContent);
  }, 100);
  return () => clearTimeout(timer);
}, [streamingContent]);

// Render menggunakan renderedContent, bukan streamingContent langsung
<MarkdownRenderer content={renderedContent} />
```

---

## 6. Streaming Reliability Layer — Ringkasan

| # | Aspek | Backend | Frontend |
|---|-------|---------|----------|
| 1 | **Disconnect Detection** | `request.is_disconnected()` setiap fase + setiap chunk | `reader.read()` catch → `onError()` |
| 2 | **Cancel / Stop** | Loop break saat disconnect, persist partial di `finally` | `AbortController.abort()`, tombol "Stop Generating" |
| 3 | **Timeout** | `generate_stream(timeout=120)` → timeout check per chunk | Safety timeout 120s di store, auto-abort |
| 4 | **Memory Safety** | Accumulate `full_text` string only, no heavy ops per chunk | Throttled render, no per-token re-render |
| 5 | **Throttled Rendering** | N/A | `setTimeout(100ms)` throttle sebelum `setRenderedContent` |
| 6 | **Partial Preservation** | Persist partial di `finally` block saat cancelled | `streamingContent` TIDAK di-reset pada error/cancel |
| 7 | **Error Standardization** | SEMUA error → `sse_event("error", {"msg": ...})`, tidak pernah silent fail | Semua error → `onError()` callback, tampil di UI |
| 8 | **State Consistency** | N/A | `isStreaming` strict true/false lifecycle, `clearStreamState()` untuk reset |

---

## 7. File yang Diubah/Ditambah

### Backend
| File | Status | Fungsi |
|------|--------|--------|
| `app/utils/sse.py` | **NEW** | SSE event formatter |
| `app/ai/gemini_provider.py` | **MODIFY** | Tambah `generate_stream()` + timeout |
| `app/api/routes/generate_doc.py` | **MODIFY** | SSE endpoint + disconnect detection |

### Frontend
| File | Status | Fungsi |
|------|--------|--------|
| `src/types/generate.ts` | **MODIFY** | `StreamDoneData` type |
| `src/api/generate.ts` | **MODIFY** | `streamGenerateFromDocument()` + AbortController |
| `src/stores/generate-store.ts` | **MODIFY** | Streaming state + cancel + timeout |
| `src/components/generate/StreamingResult.tsx` | **NEW** | Live view + throttle + partial + stop |
| `src/components/generate/GenerateContainer.tsx` | **MODIFY** | View states `streaming` + `partial` |
| `src/components/generate/UploadForm.tsx` | **MODIFY** | Panggil stream API |
| `src/i18n/locales/id.ts` | **MODIFY** | Keys baru |
| `src/i18n/locales/en.ts` | **MODIFY** | Keys baru |

---

## 8. Task Breakdown

| #   | Task                                          | Layer     | Est.   |
|-----|-----------------------------------------------|-----------|--------|
| T01 | SSE utility helper `sse_event()`              | Backend   | 15 min |
| T02 | `GeminiProvider.generate_stream()` + timeout  | Backend   | 45 min |
| T03 | SSE endpoint + disconnect detection + cancel  | Backend   | 2 jam  |
| T04 | Frontend types `StreamDoneData`               | Frontend  | 15 min |
| T05 | API client + AbortController + error handling | Frontend  | 1 jam  |
| T06 | Store: streaming state + cancel + timeout     | Frontend  | 1 jam  |
| T07 | `StreamingResult.tsx` + throttle + partial     | Frontend  | 2 jam  |
| T08 | Container + UploadForm wiring                 | Frontend  | 45 min |
| T09 | i18n + QA + Build                             | Frontend  | 30 min |

**Total: ~8.5 jam kerja**

---

## 9. Dependency Graph

```
T01 → T02 → T03                    (Backend: SSE util → Stream method → Endpoint)
                ↓
T04 → T05 → T06 → T07 → T08 → T09 (Frontend: Types → API → Store → UI)
```

---

## 10. Verification Plan

### Automated
- `npm run build` → zero errors
- Backend startup tanpa error

### Manual Test Scenarios

**Skenario 1: Happy Path — Streaming Generate**
1. Upload file → klik Generate TOR
2. Status "Memproses dokumen..." tampil sebentar
3. Status berubah ke "Menghasilkan TOR..."
4. Teks markdown muncul chunk per chunk (throttled, smooth)
5. Setelah selesai, transisi ke `GenerateResult` view
6. Export buttons berfungsi
7. History menampilkan entry baru ✓

**Skenario 2: User Cancel Mid-Stream**
1. Upload file → mulai generate
2. Setelah beberapa teks tampil, klik "Stop Generating"
3. Streaming berhenti segera
4. Partial result tampil dengan label "Hasil belum lengkap"
5. Tombol "Coba Lagi" tersedia
6. History menampilkan entry gagal

**Skenario 3: Error Mid-Stream**
1. Upload file (simulasikan Gemini error)
2. Status muncul, lalu error message tampil
3. Partial text yang sudah diterima tetap ditampilkan
4. History menampilkan entry ✗ Failed

**Skenario 4: Network Disconnect**
1. Upload file, mulai streaming
2. Cabut WiFi / kill backend
3. Frontend detect stream broken
4. Partial text tetap tampil, error message muncul
5. Tidak ada infinite loading / UI stuck

**Skenario 5: Timeout**
1. Upload file sangat besar → generate lama
2. Setelah 120 detik, auto-abort
3. Error "Timeout" tampil dengan partial result

**Skenario 6: Rapid Re-generate**
1. Generate → cancel → generate lagi
2. State di-reset dengan benar, no stale data
3. Streaming kedua berjalan normal

---

## 11. Catatan Teknis

> [!IMPORTANT]
> **Post-processing harus dilakukan SETELAH stream selesai LENGKAP**, bukan per-chunk. Post-processor butuh teks lengkap untuk validasi struktur dan word count. Jika stream di-cancel, post-processing DILEWATI.

> [!WARNING]
> **Gemini deprecated library**: Project saat ini menggunakan `google.generativeai` yang deprecated. Streaming berfungsi via `generate_content(prompt, stream=True)`. Migration ke `google.genai` bisa dilakukan di version berikutnya.

> [!CAUTION]
> **Throttled rendering WAJIB**: Tanpa throttle, setiap token akan trigger React re-render + Markdown parse. Pada dokumen 2000+ kata ini bisa menyebabkan CPU spike dan UI lag. Implementasi: accumulate raw text di store, throttle `setRenderedContent` setiap 100ms di komponen.

> [!IMPORTANT]
> **Error event standardization**: Backend TIDAK BOLEH silent fail atau return plain exception. SEMUA error → `sse_event("error", {"msg": ...})`. Frontend SEMUA error → masuk `onError()` handler, set state, tampilkan di UI. Tidak ada jalur error yang hilang.
