# Beta 0.2.6 — Streaming Chat (SSE)

## Latar Belakang

Saat ini chat menggunakan dua mekanisme transport yang keduanya bermasalah:

1. **WebSocket** (`ws_chat.py` → `StreamService`)  
   - **Fake streaming**: memanggil `process_message()` secara blocking, lalu split result per kata dengan `.split(" ")` — bukan real token stream
   - User tetap menunggu di "Thinking..." selama LLM proses keseluruhan

2. **HTTP Fallback** (`POST /hybrid`)  
   - Blocking penuh — user menunggu sampai LLM selesai generate seluruh response

### Root Cause

| # | Problem | File | Status |
|---|---------|------|--------|
| 1 | Fake streaming via word split | `stream_service.py` L53-55 | ❌ HARUS DIHAPUS |
| 2 | `OllamaProvider.chat_stream()` tidak digunakan | `ollama_provider.py` L115 | ✅ Sudah ada, dead code |
| 3 | `GeminiChatProvider` tidak punya `chat_stream()` | `gemini_chat_provider.py` | ❌ HARUS DITAMBAH |
| 4 | Tidak ada SSE endpoint untuk chat | — | ❌ HARUS DIBUAT |

---

## Keputusan Arsitektur (FINAL — TIDAK BOLEH DIUBAH)

### 1. Transport: SSE Primary, WebSocket Fallback

```
PRIMARY:   POST /hybrid/stream  →  SSE (text/event-stream)
FALLBACK:  WebSocket /ws/chat    →  Hanya jika SSE gagal/tidak tersedia
```

- WebSocket **TIDAK DIHAPUS** — file `ws_chat.py`, `socket.ts`, `useWebSocket.ts` tetap ada
- WebSocket **TIDAK LAGI menjadi primary** — frontend WAJIB coba SSE dulu
- Semua fake streaming di `StreamService` **DIHAPUS**

### 2. Real Token Streaming — Zero Fake

```
DILARANG:
  - .split(" ") dari response lengkap
  - Simulasi token delay
  - Buffer seluruh response lalu kirim sekaligus

WAJIB:
  - Setiap token dari LLM langsung di-yield ke client
  - OllamaProvider.chat_stream() → real async generator
  - GeminiChatProvider.chat_stream() → real async generator
```

### 3. Provider Interface Standar

Kedua provider HARUS expose interface identik:

```python
async def chat_stream(self, messages: list[dict], think: bool = True) -> AsyncGenerator[dict, None]:
    """Yield: {"token": str, "thinking": str, "done": bool}"""
```

**Rule Thinking vs Token:**

```
Jika provider SUPPORT thinking (Ollama dengan model yang punya thinking):
  → yield {"thinking": "...", "token": "", "done": false}   ← fase thinking
  → yield {"thinking": "", "token": "...", "done": false}   ← fase output

Jika provider TIDAK support thinking (Gemini, atau Ollama tanpa thinking):
  → yield {"thinking": "", "token": "...", "done": false}   ← langsung output
  → SKIP fase thinking sepenuhnya
  → Frontend TIDAK akan menampilkan ThinkingIndicator
```

> Provider **TIDAK BOLEH memalsukan thinking**. Jika LLM tidak mengirim thinking token, yield `thinking: ""` dan langsung gunakan `token` sebagai output utama.

### 4. Backend Streaming Flow

```
1. yield {"type": "status", "msg": "...", "session_id": "uuid"}
2. IF provider support thinking:
     yield {"type": "thinking", "t": "..."}     ← per token dari thinking
   ELSE:
     SKIP — langsung ke step 3
3. yield {"type": "token", "t": "..."}         ← per token REAL dari LLM
4. Accumulate full response text dari semua token
5. Parse JSON dari accumulated text
6. yield {"type": "done", "session_id": "...", "message": "...", "state": {...}, ...}
7. Jika gagal → yield {"type": "error", "msg": "..."}
```

### 5. Frontend Strategy

```
sendMessage() flow:
  1. Coba SSE via sendMessageStream()
  2. Jika SSE gagal → fallback ke WebSocket (existing)
  3. Jika WS juga gagal → fallback ke HTTP blocking (existing)

State management TIDAK BERUBAH:
  - appendToken()      → sudah ada
  - setThinking()      → sudah ada
  - finalizeStream()   → sudah ada
  - setError()         → sudah ada
```

### 6. UX Requirement

- User HARUS melihat transisi: **thinking → streaming token → done**
- Token muncul **real-time** per karakter/kata dari LLM
- **TIDAK BOLEH** ada loading lama tanpa output
- **TIDAK BOLEH** ada fake typing animation

---

## Proposed Changes

### Backend

---

#### [MODIFY] [ollama_provider.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/ai/ollama_provider.py)

`chat_stream()` sudah ada (L115-150) tapi perlu perbaikan:
- **Hapus `format: "json"` dari streaming mode** — token stream tidak bisa di-parse sebagai JSON per-chunk, format JSON hanya untuk response final
- **Tambah `asyncio.wait_for` timeout wrapper** — supaya tidak hang jika Ollama freeze
- **Pastikan yield format konsisten**: `{"token": str, "thinking": str, "done": bool}`

#### [MODIFY] [gemini_chat_provider.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/ai/gemini_chat_provider.py)

- **Tambah `chat_stream()`** — async generator menggunakan Gemini Streaming API
- Output format **IDENTIK** dengan `OllamaProvider.chat_stream()`
- Gunakan `generate_content(stream=True)` atau equivalent dari Gemini SDK

#### [MODIFY] [chat_service.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/services/chat_service.py)

- **Tambah `process_message_stream()`** — async generator version
- **TIDAK BOLEH** memanggil `process_message()` (blocking) di dalam stream
- Flow:
  1. Session lookup/create (sama seperti `process_message`)
  2. Build prompt (sama)
  3. `yield StreamEvent(type="thinking_start")`
  4. **Loop `provider.chat_stream()`** — yield setiap token asli:
     - Thinking token → `yield StreamEvent(type="thinking_token", token=t)`
     - Content token → `yield StreamEvent(type="token", token=t)`
  5. Accumulate full response text
  6. Parse JSON dari accumulated text (reuse `_call_with_retry` logic)
  7. Update session (sama)
  8. `yield StreamEvent(type="done", response={...})`
  9. Jika parse gagal → `yield StreamEvent(type="error", error="...")`

#### [MODIFY] [stream_service.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/services/stream_service.py)

- **HAPUS fake streaming** — hapus `words = response_text.split(" ")` dan loop per-word
- **Ganti dengan delegasi ke `ChatService.process_message_stream()`**
- Atau: hapus `StreamService` sepenuhnya jika `process_message_stream()` di ChatService sudah cukup

#### [NEW/MODIFY] SSE Endpoint

File: [hybrid.py](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app/api/routes/hybrid.py) (tambah endpoint baru)

- **`POST /hybrid/stream`** — menerima JSON body (`HybridRequest`), return `StreamingResponse(media_type="text/event-stream")`
- Format SSE konsisten:
  ```
  data: {"type": "status", "msg": "...", "session_id": "..."}\n\n
  data: {"type": "thinking", "t": "..."}\n\n
  data: {"type": "token", "t": "..."}\n\n
  data: {"type": "done", "session_id": "...", "message": "...", "state": {...}}\n\n
  data: {"type": "error", "msg": "..."}\n\n
  ```
- **WAJIB handle**:
  - Client disconnect detection (`await request.is_disconnected()`)
  - Error standardization (semua error → SSE error event, bukan HTTP 500)

---

### Frontend

---

#### [MODIFY] [chat.ts](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/api/chat.ts)

- **Tambah `sendMessageStream()`** — SSE consumer
- Gunakan pola `consumeStream` yang sudah ada di `generate.ts`
- Callbacks: `onThinking(t)`, `onToken(t)`, `onDone(data)`, `onError(msg)`, `onStatus(msg, sessionId)`

#### [MODIFY] [chat-store.ts](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/stores/chat-store.ts)

- Update `sendMessage()`:
  ```
  PRIMARY:  await sendMessageStream({...}, callbacks, abortSignal)
  FALLBACK: if WS connected → ws.send(text)
  FALLBACK: if both fail → await apiSendMessage({...}) (existing HTTP)
  ```
- **Tambah `_abortController`** untuk cancel stream (opsional, jika tombol Stop ingin ditambahkan nanti)
- State actions yang sudah ada **TIDAK DIUBAH** — hanya sumber event yang berubah dari WS ke SSE

#### UI Components — TIDAK ADA PERUBAHAN BESAR

- [ChatArea.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/ChatArea.tsx) — sudah support streaming via `stream.partialContent`
- [MessageBubble.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/MessageBubble.tsx) — sudah support `status: "streaming"` → `StreamingText`
- [StreamingText.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/StreamingText.tsx) — sudah render cursor blinking
- [ThinkingIndicator.tsx](file:///d:/Iman874/Documents/Github/ai-agent-hybrid/app_frontend/src/components/chat/ThinkingIndicator.tsx) — sudah ada

#### WebSocket Files — TIDAK DIHAPUS, TIDAK DIMODIFIKASI

- `ws_chat.py` → tetap
- `socket.ts` → tetap
- `useWebSocket.ts` → tetap
- Hanya tidak lagi diprioritaskan di `sendMessage()`

---

## Task Breakdown

| Task | Judul | Scope |
|------|-------|-------|
| **1** | Provider Streaming: Ollama fix + Gemini `chat_stream()` | Backend — `ollama_provider.py`, `gemini_chat_provider.py` |
| **2** | `process_message_stream()` di ChatService | Backend — `chat_service.py`, hapus fake stream di `stream_service.py` |
| **3** | SSE endpoint `POST /hybrid/stream` | Backend — `hybrid.py`, disconnect detection, error handling |
| **4** | API client `sendMessageStream()` | Frontend — `chat.ts`, reuse `consumeStream` pattern |
| **5** | Store SSE migration + fallback chain | Frontend — `chat-store.ts`, SSE primary → WS fallback → HTTP fallback |
| **6** | Testing, edge cases & polish | QA — timeout, provider switching, disconnect, i18n |
| **7** | Thinking UI reveal controls | Frontend — reasoning hide/show + expand/collapse di chat bubble |

---

## Validation Checklist

Setelah implementasi selesai, SEMUA harus terpenuhi:

- [x] **Tidak ada fake streaming** — `stream_service.py` tidak lagi split kata
- [x] **Tidak ada blocking response** di path SSE — `process_message()` tidak dipanggil dari stream
- [x] **SSE adalah primary** — `sendMessage()` di store panggil SSE duluan
- [x] **Token real-time** — user langsung lihat karakter muncul saat LLM generate
- [x] **Thinking → streaming transisi mulus** — tidak ada delay gap
- [x] **WebSocket masih ada** — sebagai fallback, bukan primary
- [x] **Provider interface standar** — Ollama dan Gemini sama-sama expose `chat_stream()`
- [x] **Disconnect handled** — client abort tidak crash server
- [x] **Build clean** — `npm run build` sukses, `uvicorn` reload tanpa error

---

## Verification Plan

### Automated
- Backend: `curl -X POST /hybrid/stream` → verifikasi SSE event format
- Frontend: `npm run build` clean

### Manual
- **Real-time test**: Kirim pesan chat → token harus muncul live satu per satu (bukan muncul sekaligus)
- **Speed comparison**: Bandingkan perceived latency SSE vs HTTP blocking lama
- **Provider switch**: Test stream chat di mode Ollama DAN mode Gemini
- **Error handling**: Matikan Ollama di tengah streaming → pastikan error graceful
- **Session sync**: Pastikan `session_id` ter-sync setelah stream selesai
- **Fallback**: Disable SSE endpoint → pastikan WS fallback bekerja
