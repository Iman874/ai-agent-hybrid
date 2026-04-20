# Task 3: SSE Endpoint + Disconnect Detection + Cancel

## 1. Judul Task
Buat endpoint `POST /generate/from-document/stream` yang mengembalikan SSE stream, lengkap dengan disconnect detection dan cancel handling.

## 2. Deskripsi
Endpoint utama streaming. Menerima file upload yang sama seperti endpoint blocking, tapi mengembalikan `StreamingResponse` bertipe `text/event-stream`. Setiap fase (parse, prompt, generate) mengirim status event, lalu streaming token per token dari Gemini. Dilengkapi pengecekan disconnect client di setiap fase dan setiap chunk.

## 3. Tujuan Teknis
- Endpoint `POST /generate/from-document/stream` → `StreamingResponse`
- Alur event: `status` → `status` → `status` → `token`×N → `done`
- `request.is_disconnected()` dicek di setiap fase dan setiap chunk
- Semua error → `sse_event("error", ...)`, tidak pernah silent fail
- Jika cancelled, persist partial result di `finally` block
- Post-processing HANYA dilakukan setelah stream selesai LENGKAP

## 4. Scope
### Yang dikerjakan
- Tambah endpoint baru di `app/api/routes/generate_doc.py`
- Import `StreamingResponse` dari `fastapi.responses`
- Import `sse_event` dari `app/utils/sse`

### Yang tidak dikerjakan
- Tidak mengubah endpoint blocking yang sudah ada
- Tidak mengubah frontend (task 5-8)

## 5. Langkah Implementasi

### Step 1: Tambah imports di `generate_doc.py`

```python
import json
from fastapi.responses import StreamingResponse
from app.utils.sse import sse_event
```

### Step 2: Tambah endpoint setelah endpoint blocking (sebelum endpoint history)

```python
@router.post("/generate/from-document/stream")
async def generate_from_document_stream(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber"),
    context: str = Form("", description="Konteks tambahan"),
    style_id: str | None = Form(None, description="ID style TOR"),
):
    """Generate TOR dari dokumen — streaming via SSE.

    Event types:
    - status: {"type":"status","msg":"..."} — progress status
    - token: {"type":"token","t":"..."} — text chunk dari Gemini
    - done: {"type":"done","session_id":"...","metadata":{...}} — selesai
    - error: {"type":"error","msg":"..."} — error
    """
    gemini = request.app.state.gemini_provider
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)
    style_manager = request.app.state.style_manager
    doc_gen_repo = request.app.state.doc_gen_repo

    # Step 1: Read file
    file_bytes = await file.read()
    filename = file.filename or "unknown.txt"
    session_id = f"doc-{uuid.uuid4().hex[:8]}"

    # Step 2: Resolve style
    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except StyleNotFoundError:
            raise HTTPException(status_code=404, detail=f"Style '{style_id}' tidak ditemukan.")
    else:
        active_style = style_manager.get_active_style()

    # Step 3: Persist processing record
    await doc_gen_repo.create(
        gen_id=session_id,
        filename=filename,
        file_size=len(file_bytes),
        context=context,
        style_id=getattr(active_style, 'id', style_id),
        style_name=getattr(active_style, 'name', None),
    )

    async def event_stream():
        full_text = ""
        cancelled = False

        try:
            # Phase 1: Parse document
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Memproses dokumen..."})
            document_text = await DocumentParser.parse(file_bytes, filename)

            # Phase 2: RAG + Prompt
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Menyusun prompt..."})

            rag_examples = None
            if rag_pipeline:
                try:
                    rag_examples = await rag_pipeline.retrieve(document_text[:200], top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")

            format_spec = active_style.to_prompt_spec()
            prompt = GeminiPromptBuilder.build_from_document(
                document_text=document_text,
                user_context=context,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )

            # Phase 3: Stream Gemini
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Menghasilkan TOR..."})

            async for chunk in gemini.generate_stream(prompt):
                if await request.is_disconnected():
                    cancelled = True
                    break

                full_text += chunk
                yield sse_event("token", {"t": chunk})

            # Jika cancelled mid-stream, JANGAN post-process
            if cancelled:
                return

            # Phase 4: Post-process (hanya jika stream selesai lengkap)
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

            # Store di cache untuk export endpoint
            tor_doc = TORDocument(
                content=processed.content,
                metadata=TORMetadata(
                    **tor_metadata,
                    generation_time_ms=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                ),
            )
            tor_cache = request.app.state.tor_cache
            await tor_cache.store(session_id, tor_doc)

            # Phase 6: Done event
            yield sse_event("done", {
                "session_id": session_id,
                "metadata": tor_metadata,
            })

            logger.info(
                f"TOR streamed: file={filename}, "
                f"words={processed.word_count}"
            )

        except Exception as e:
            # SEMUA error → SSE error event
            logger.error(f"Stream generate error: {e}")
            await doc_gen_repo.update_failed(session_id, str(e)[:500])
            yield sse_event("error", {"msg": str(e)[:300]})

        finally:
            # Jika cancelled dan ada partial text, persist partial failure
            if cancelled and full_text:
                try:
                    await doc_gen_repo.update_failed(
                        session_id,
                        f"Dibatalkan oleh user. Partial: {len(full_text)} chars"
                    )
                except Exception:
                    pass  # Best-effort persist

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

## 6. Output yang Diharapkan

```
# curl -X POST http://localhost:8000/api/v1/generate/from-document/stream \
#   -F "file=@test.pdf" -F "context=Buat TOR 2026"

data: {"type": "status", "msg": "Memproses dokumen..."}

data: {"type": "status", "msg": "Menyusun prompt..."}

data: {"type": "status", "msg": "Menghasilkan TOR..."}

data: {"type": "token", "t": "# "}

data: {"type": "token", "t": "TOR Kegiatan "}

data: {"type": "token", "t": "Pelatihan AI"}

...

data: {"type": "done", "session_id": "doc-abc123", "metadata": {"word_count": 1240, "generated_by": "gemini-2.0-flash", "mode": "standard", "has_assumptions": false}}
```

## 7. Dependencies
- Task 1 (SSE utility)
- Task 2 (generate_stream method)

## 8. Acceptance Criteria
- [ ] Endpoint `POST /generate/from-document/stream` ada dan mengembalikan `text/event-stream`
- [ ] Event alur: `status` → `status` → `status` → `token`×N → `done`
- [ ] `request.is_disconnected()` dicek setiap fase DAN setiap chunk
- [ ] Jika client disconnect, loop berhenti bersih tanpa error spam
- [ ] Jika cancelled mid-stream, partial text di-persist sebagai failed
- [ ] Post-processing HANYA terjadi setelah stream selesai lengkap
- [ ] Semua error → `sse_event("error", ...)`, tidak pernah silent fail
- [ ] Endpoint blocking lama TIDAK berubah
- [ ] Record `document_generations` ter-persist (processing → completed/failed)
- [ ] Backend restart tanpa error

## 9. Estimasi
**High** (~2 jam)
