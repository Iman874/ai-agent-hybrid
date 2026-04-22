# Task 01 — Backend: Endpoint SSE `POST /generate/chat/stream`

## 1. Judul Task

Membuat endpoint SSE baru untuk streaming TOR generation dari sesi chat.

## 2. Deskripsi

Saat ini, `POST /generate` bersifat blocking — ia memanggil Gemini, menunggu respons penuh, lalu mengirim JSON sekaligus. Task ini menambahkan endpoint streaming baru `POST /generate/chat/stream` yang mengambil data dari **sesi chat** (bukan file upload), lalu men-stream token TOR via SSE sama seperti `POST /generate/from-document/stream`.

## 3. Tujuan Teknis

- Endpoint baru `POST /generate/chat/stream` menerima body `GenerateRequest` (sudah ada di `app/models/generate.py`).
- Endpoint membaca `session`, `extracted_data`, dan `chat_history` dari DB via `SessionManager`.
- Membangun prompt via `GeminiPromptBuilder` (meniru logic di `GenerateService.generate_tor()` lines 82–107).
- Men-stream token via `GeminiProvider.generate_stream()`.
- Semua fase mempunyai disconnect detection via `request.is_disconnected()`.
- Post-processing dilakukan **setelah** stream selesai lengkap.
- Persist ke DB & cache, update session state ke `COMPLETED`.
- Setiap error → `sse_event("error", ...)`, zero silent fail.

## 4. Scope

### Yang dikerjakan
- Menambahkan fungsi `generate_tor_from_chat_stream()` di `app/api/routes/generate.py`.
- Mereplikasi pipeline logic dari `GenerateService.generate_tor()` namun dalam bentuk streaming generator.
- Memasukkan cost logging via `CostController.log_call()`.
- Memasukkan cache via `TORCache.store()`.

### Yang tidak dikerjakan
- Perubahan frontend (task terpisah).
- Perubahan pada `GeminiProvider.generate_stream()` (sudah ada dan fungsional).
- Perubahan pada endpoint blocking `POST /generate` (dipertahankan sebagai fallback).

## 5. Langkah Implementasi

### Step 1: Buka `app/api/routes/generate.py`

Tambahkan import yang diperlukan di bagian atas:

```python
from fastapi.responses import StreamingResponse
from fastapi import Request
import time
import json
from app.utils.sse import sse_event
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history
from app.models.generate import TORDocument, TORMetadata
from app.utils.errors import GeminiTimeoutError
```

### Step 2: Tambahkan endpoint baru setelah endpoint `/generate` yang ada

```python
@router.post("/generate/chat/stream")
async def generate_tor_from_chat_stream(request: Request, body: GenerateRequest):
    """
    Streaming TOR generation dari sesi chat.
    Menggunakan SSE untuk men-stream token Gemini secara real-time.
    """
    # Ambil semua dependency dari app.state
    session_mgr = request.app.state.session_mgr
    gemini = request.app.state.gemini_provider
    cost_ctrl = request.app.state.generate_service.cost_ctrl
    prompt_builder = request.app.state.generate_service.prompt_builder
    post_processor = request.app.state.generate_service.post_processor
    tor_cache = request.app.state.tor_cache
    style_manager = request.app.state.style_manager
    rag_pipeline = request.app.state.rag_pipeline

    async def event_stream():
        full_text = ""
        cancelled = False
        start_time = time.monotonic()

        try:
            # === Phase 1: Load session data ===
            if await request.is_disconnected():
                cancelled = True; return
            yield sse_event("status", {"msg": "Memeriksa data sesi chat..."})

            session = await session_mgr.get(body.session_id)
            data = session.extracted_data
            history = await session_mgr.get_chat_history(body.session_id)

            # Validasi: cek kelengkapan data
            if body.mode == "standard" and session.completeness_score < 0.3:
                yield sse_event("error", {
                    "msg": f"Data belum cukup (skor: {session.completeness_score:.0%}). "
                           "Lanjutkan chat untuk melengkapi informasi."
                })
                return

            # === Phase 2: RAG + Style + Prompt ===
            if await request.is_disconnected():
                cancelled = True; return
            yield sse_event("status", {"msg": "Menyusun instruksi untuk AI..."})

            # RAG examples (opsional)
            rag_examples = None
            if rag_pipeline and data.judul:
                try:
                    rag_examples = await rag_pipeline.retrieve(data.judul, top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without: {e}")

            # Format style
            active_style = style_manager.get_active_style()
            format_spec = active_style.to_prompt_spec()

            # Build prompt (replika logic dari GenerateService)
            if body.mode == "standard":
                prompt = prompt_builder.build_standard(
                    data=data,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )
            else:
                formatted_history = format_chat_history(history)
                prompt = prompt_builder.build_escalation(
                    chat_history=formatted_history,
                    partial_data=data,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )

            # === Phase 3: Stream Gemini ===
            if await request.is_disconnected():
                cancelled = True; return
            yield sse_event("status", {"msg": "Mulai membuat dokumen TOR..."})

            # Update session state ke GENERATING
            await session_mgr.update(body.session_id, state="GENERATING")

            async for chunk in gemini.generate_stream(prompt):
                if await request.is_disconnected():
                    cancelled = True
                    break
                full_text += chunk
                yield sse_event("token", {"t": chunk})

            if cancelled:
                return

            # === Phase 4: Post-processing ===
            yield sse_event("status", {"msg": "Merapikan format dokumen..."})
            processed = post_processor.process(full_text, style=active_style)

            # === Phase 5: Persist ke DB & Cache ===
            duration_ms = int((time.monotonic() - start_time) * 1000)

            tor_metadata = {
                "generated_by": gemini.model_name,
                "mode": body.mode,
                "word_count": processed.word_count,
                "has_assumptions": processed.has_assumptions,
            }

            tor_doc = TORDocument(
                content=processed.content,
                metadata=TORMetadata(
                    generated_by=gemini.model_name,
                    mode=body.mode,
                    word_count=processed.word_count,
                    generation_time_ms=duration_ms,
                    has_assumptions=processed.has_assumptions,
                    prompt_tokens=0,
                    completion_tokens=0,
                ),
            )

            await tor_cache.store(body.session_id, tor_doc)
            await cost_ctrl.log_call(
                body.session_id, gemini.model_name, body.mode,
                0, 0, duration_ms, success=True,
            )
            await session_mgr.update(
                body.session_id,
                state="COMPLETED",
                generated_tor=processed.content,
                gemini_calls_count=session.gemini_calls_count + 1,
            )

            # === Phase 6: Done event ===
            yield sse_event("done", {
                "session_id": body.session_id,
                "metadata": tor_metadata,
            })

        except GeminiTimeoutError as e:
            logger.error(f"Gemini stream timeout: {e}")
            await session_mgr.update(body.session_id, state="READY")
            yield sse_event("error", {"msg": f"Timeout saat generate: {e}"})

        except Exception as e:
            logger.error(f"Chat stream generate error: {e}")
            await session_mgr.update(body.session_id, state="READY")
            yield sse_event("error", {"msg": str(e)[:300]})

        finally:
            if cancelled and full_text:
                logger.info(
                    f"Generate cancelled mid-stream: session={body.session_id}, "
                    f"partial={len(full_text)} chars"
                )
                await session_mgr.update(body.session_id, state="READY")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

### Step 3: Verifikasi path resolusi `app.state`

Buka `app/main.py` dan pastikan semua attribute yang dibutuhkan sudah tersedia di `app.state`:
- `app.state.session_mgr` ✅ (line 38)
- `app.state.gemini_provider` ✅ (line 66)
- `app.state.generate_service` ✅ (line 73) — `.cost_ctrl`, `.prompt_builder`, `.post_processor` diakses dari sini
- `app.state.tor_cache` ✅ (line 86)
- `app.state.style_manager` ✅ (line 71)
- `app.state.rag_pipeline` ✅ (line 43)

**Semua sudah terdaftar.** Tidak ada penambahan state baru yang diperlukan.

## 6. Output yang Diharapkan

### Request
```http
POST /api/v1/generate/chat/stream
Content-Type: application/json

{
  "session_id": "abc-123",
  "mode": "standard"
}
```

### Response (SSE stream)
```
data: {"type": "status", "msg": "Memeriksa data sesi chat..."}

data: {"type": "status", "msg": "Menyusun instruksi untuk AI..."}

data: {"type": "status", "msg": "Mulai membuat dokumen TOR..."}

data: {"type": "token", "t": "# "}

data: {"type": "token", "t": "Kerangka Acuan Kerja"}

data: {"type": "token", "t": "\n\n## "}

... (ratusan token) ...

data: {"type": "status", "msg": "Merapikan format dokumen..."}

data: {"type": "done", "session_id": "abc-123", "metadata": {"generated_by": "gemini-2.0-flash", "mode": "standard", "word_count": 1240, "has_assumptions": false}}
```

## 7. Dependencies

- Tidak ada dependency ke task lain. Task ini adalah **titik awal** (root) dari seluruh rantai implementasi.

## 8. Acceptance Criteria

- [ ] Endpoint `POST /generate/chat/stream` ter-register dan accessible via `/api/v1/generate/chat/stream`.
- [ ] Menerima body `GenerateRequest` (`session_id`, `mode`, `force_regenerate`).
- [ ] Memancarkan event SSE berformat `data: {"type": "..."}\n\n`.
- [ ] Event types: `status`, `token`, `done`, `error`.
- [ ] Disconnect detection (`request.is_disconnected()`) di setiap fase dan setiap loop chunk.
- [ ] Jika mode `standard` tapi `completeness_score < 0.3`, langsung emit `error` event.
- [ ] Prompt building mendukung `standard` dan `escalation` mode.
- [ ] Post-processing dilakukan SETELAH stream selesai lengkap.
- [ ] Session state di-update ke `GENERATING` saat mulai stream, `COMPLETED` saat done, rollback ke `READY` saat error/cancel.
- [ ] TOR di-persist ke cache dan DB.
- [ ] Cost logging via `CostController.log_call()`.
- [ ] Semua error → `sse_event("error", ...)`, tidak pernah silent fail.
- [ ] Backend startup tanpa import error.

## 9. Estimasi

**Medium** — ~2 jam kerja (replikasi logic dari `GenerateService` + membungkus dalam SSE generator).
