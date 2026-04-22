import logging
import uuid
import json
import asyncio
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from app.core.document_parser import DocumentParser
from app.core.gemini_prompt_builder import GeminiPromptBuilder
from app.core.style_manager import StyleNotFoundError
from app.models.generate import TORDocument, TORMetadata, GenerateResponse
from app.utils.errors import DocumentParseError, GeminiTimeoutError
from app.utils.sse import sse_event

logger = logging.getLogger("ai-agent-hybrid.api.generate_doc")

router = APIRouter()


@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
    style_id: str | None = Form(None, description="ID style TOR spesifik (default=aktif)"),
):
    """
    Generate TOR dari dokumen yang diupload.

    - **file**: Dokumen sumber (PDF, TXT, MD, DOCX). Maks 20MB.
    - **context**: Konteks tambahan, misal "Buat TOR lanjutan 2026".
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

    # Step 2: Get active style
    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except StyleNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Style '{style_id}' not found.",
            )
    else:
        active_style = style_manager.get_active_style()

    # Step 3: Persist record (status=processing)
    await doc_gen_repo.create(
        gen_id=session_id,
        filename=filename,
        file_size=len(file_bytes),
        context=context,
        style_id=getattr(active_style, 'id', style_id),
        style_name=getattr(active_style, 'name', None),
    )

    try:
        # Step 4: Parse document → text
        document_text = await DocumentParser.parse(file_bytes, filename)

        # Step 5: RAG (optional — retrieve style examples)
        rag_examples = None
        if rag_pipeline:
            try:
                query = document_text[:200]
                rag_examples = await rag_pipeline.retrieve(query, top_k=2)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        format_spec = active_style.to_prompt_spec()

        # Step 6: Build prompt
        prompt = GeminiPromptBuilder.build_from_document(
            document_text=document_text,
            user_context=context,
            rag_examples=rag_examples,
            format_spec=format_spec,
        )

        # Step 7: Call Gemini
        gemini_response = await gemini.generate(prompt)

        # Step 8: Post-process
        processed = post_processor.process(gemini_response.text, style=active_style)

        tor_doc = TORDocument(
            content=processed.content,
            metadata=TORMetadata(
                generated_by=gemini.model_name,
                mode="standard",
                word_count=processed.word_count,
                generation_time_ms=gemini_response.duration_ms,
                has_assumptions=processed.has_assumptions,
                prompt_tokens=gemini_response.prompt_tokens,
                completion_tokens=gemini_response.completion_tokens,
            ),
        )

        # Step 9: Persist completed
        import json
        await doc_gen_repo.update_completed(
            session_id,
            tor_content=processed.content,
            metadata_json=json.dumps(tor_doc.metadata.model_dump()),
        )

        # Simpan TOR ke cache agar bisa diakses oleh export endpoint lama
        tor_cache = request.app.state.tor_cache
        await tor_cache.store(session_id, tor_doc)

        logger.info(
            f"TOR from document: file={filename}, "
            f"chars={len(document_text)}, words={processed.word_count}, "
            f"time={gemini_response.duration_ms}ms"
        )

        return GenerateResponse(
            session_id=session_id,
            message=f"TOR successfully generated from document '{filename}'.",
            tor_document=tor_doc,
            cached=False,
        )

    except Exception as e:
        # Step 10: Persist failure
        await doc_gen_repo.update_failed(session_id, str(e)[:500])
        raise


@router.post("/generate/from-document/stream")
async def generate_from_document_stream(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
    style_id: str | None = Form(None, description="ID style TOR spesifik (default=aktif)"),
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
            raise HTTPException(status_code=404, detail=f"Style '{style_id}' not found.")
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
            yield sse_event("status", {"msg": "Processing document...", "session_id": session_id})
            document_text = await DocumentParser.parse(file_bytes, filename)
            await doc_gen_repo.update_source_text(session_id, document_text)

            # Phase 2: RAG + Prompt
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Building prompt..."})

            rag_examples = None
            if rag_pipeline:
                try:
                    query = document_text[:200]
                    rag_examples = await rag_pipeline.retrieve(query, top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without: {e}")

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
            yield sse_event("status", {"msg": "Generating TOR..."})

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

        except GeminiTimeoutError as e:
            await doc_gen_repo.update_failed(session_id, f"Timeout: {e}")
            yield sse_event("error", {"msg": f"Generation timeout ({e})"})

        except asyncio.CancelledError:
            cancelled = True
            logger.info("Client disconnected during stream (CancelledError)")

        except GeneratorExit:
            cancelled = True
            logger.info("Client disconnected during stream (GeneratorExit)")

        except Exception as e:
            # SEMUA error → SSE error event
            if type(e).__name__ == "ClientDisconnect":
                cancelled = True
            else:
                logger.error(f"Stream generate error: {e}")
                await doc_gen_repo.update_failed(session_id, str(e)[:500])
                yield sse_event("error", {"msg": str(e)[:300]})

        finally:
            # Pastikan selalu mengupdate database saat dibatalkan, sekalipun text masih kosong
            if cancelled:
                try:
                    msg = f"Cancelled by user. Partial: {len(full_text)} chars" if full_text else "Cancelled by user before output."
                    await doc_gen_repo.update_failed(
                        session_id,
                        msg,
                        partial_content=full_text if full_text else None,
                    )
                except Exception as e:
                    logger.error(f"Gagal update_failed database: {e}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


from app.models.generate import DocGenListItem, DocGenDetail

@router.get("/generate/history", response_model=list[DocGenListItem])
async def list_generations(request: Request, limit: int = 30):
    """List riwayat generate dari dokumen, urut terbaru."""
    doc_gen_repo = request.app.state.doc_gen_repo
    rows = await doc_gen_repo.list_all(limit=limit)

    return [
        DocGenListItem(
            id=r["id"],
            filename=r["filename"],
            file_size=r["file_size"],
            style_name=r.get("style_name"),
            status=r["status"],
            word_count=r.get("word_count"),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/generate/{gen_id}", response_model=DocGenDetail)
async def get_generation(gen_id: str, request: Request):
    """Ambil detail satu generate result."""
    doc_gen_repo = request.app.state.doc_gen_repo
    row = await doc_gen_repo.get(gen_id)

    if not row:
        raise HTTPException(status_code=404, detail="Record not found")

    metadata = None
    if row.get("metadata"):
        try:
            metadata = TORMetadata(**row["metadata"])
        except Exception:
            pass

    return DocGenDetail(
        id=row["id"],
        filename=row["filename"],
        file_size=row["file_size"],
        context=row.get("context", ""),
        style_name=row.get("style_name"),
        status=row["status"],
        tor_content=row.get("tor_content"),
        metadata=metadata,
        error_message=row.get("error_message"),
        created_at=row["created_at"],
    )


@router.delete("/generate/{gen_id}")
async def delete_generation(gen_id: str, request: Request):
    """Hapus record riwayat generate."""
    doc_gen_repo = request.app.state.doc_gen_repo
    success = await doc_gen_repo.delete(gen_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "deleted", "id": gen_id}


from pydantic import BaseModel

class SavePartialRequest(BaseModel):
    content: str
    error: str = "Cancelled by user"

@router.patch("/generate/{gen_id}/save-partial")
async def save_partial_content(gen_id: str, body: SavePartialRequest, request: Request):
    """Simpan partial content dari frontend saat stream dibatalkan.
    
    Endpoint ini dipanggil oleh frontend yang sudah punya accumulated
    streamingContent di memory saat user menekan Stop.
    Ini JAUH lebih reliable daripada mengandalkan backend finally block.
    """
    doc_gen_repo = request.app.state.doc_gen_repo
    row = await doc_gen_repo.get(gen_id)
    if not row:
        raise HTTPException(status_code=404, detail="Record not found")

    # Hanya update jika masih processing (belum di-update oleh backend)
    if row["status"] == "processing":
        await doc_gen_repo.update_failed(
            gen_id,
            error_message=body.error[:500],
            partial_content=body.content if body.content else None,
        )
        logger.info(f"Partial content saved by frontend: {gen_id}, {len(body.content)} chars")

    return {"status": "saved", "id": gen_id}


@router.post("/generate/{gen_id}/retry-stream")
async def retry_generation_stream(gen_id: str, request: Request):
    """Generate ulang TOR dari awal menggunakan source_text yang tersimpan."""
    doc_gen_repo = request.app.state.doc_gen_repo
    gemini = request.app.state.gemini_provider
    style_manager = request.app.state.style_manager
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)

    # 1. Ambil record lama
    old_row = await doc_gen_repo.get(gen_id)
    if not old_row:
        raise HTTPException(status_code=404, detail="Record not found")

    source_text = old_row.get("source_text")
    if not source_text:
        raise HTTPException(status_code=400, detail="generate.source_unavailable")

    # 2. Setup metadata riwayat baru
    session_id = f"doc-{uuid.uuid4().hex[:8]}"
    filename = old_row["filename"]
    context = old_row.get("context", "")
    style_id = old_row.get("style_id")

    # 3. Resolve style
    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except StyleNotFoundError:
            active_style = style_manager.get_active_style()
    else:
        active_style = style_manager.get_active_style()

    # 4. Buat record baru
    await doc_gen_repo.create(
        gen_id=session_id,
        filename=filename,
        file_size=old_row["file_size"],
        context=context,
        style_id=getattr(active_style, 'id', style_id),
        style_name=getattr(active_style, 'name', None),
    )
    await doc_gen_repo.update_source_text(session_id, source_text)

    async def event_stream():
        full_text = ""
        cancelled = False
        try:
            yield sse_event("status", {"msg": "Preparing retry...", "session_id": session_id})
            if await request.is_disconnected():
                cancelled = True
                return

            rag_examples = None
            if rag_pipeline:
                try:
                    query = source_text[:200]
                    rag_examples = await rag_pipeline.retrieve(query, top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without: {e}")

            format_spec = active_style.to_prompt_spec()
            prompt = GeminiPromptBuilder.build_from_document(
                document_text=source_text,
                user_context=context,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )

            yield sse_event("status", {"msg": "Generating TOR..."})
            async for chunk in gemini.generate_stream(prompt):
                if await request.is_disconnected():
                    cancelled = True
                    break
                full_text += chunk
                yield sse_event("token", {"t": chunk})

            if cancelled:
                return

            processed = post_processor.process(full_text, style=active_style)
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
            
            # Update history lama supaya hilang jika sukses (optional, tp UX lebih bagus)
            await doc_gen_repo.delete(gen_id)

            yield sse_event("done", {
                "session_id": session_id,
                "metadata": tor_metadata,
            })

        except GeminiTimeoutError as e:
            await doc_gen_repo.update_failed(session_id, f"Timeout: {e}")
            yield sse_event("error", {"msg": f"Generation timeout ({e})"})
        except asyncio.CancelledError:
            cancelled = True
        except GeneratorExit:
            cancelled = True
        except Exception as e:
            if type(e).__name__ == "ClientDisconnect":
                cancelled = True
            else:
                await doc_gen_repo.update_failed(session_id, str(e)[:500])
                yield sse_event("error", {"msg": str(e)[:300]})
        finally:
            if cancelled:
                try:
                    msg = f"Cancelled by user. Partial: {len(full_text)} chars" if full_text else "Cancelled by user."
                    await doc_gen_repo.update_failed(session_id, msg, partial_content=full_text if full_text else None)
                except Exception:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/generate/{gen_id}/continue-stream")
async def continue_generation_stream(gen_id: str, request: Request):
    """Lanjutkan TOR yang terputus."""
    doc_gen_repo = request.app.state.doc_gen_repo
    gemini = request.app.state.gemini_provider
    style_manager = request.app.state.style_manager
    post_processor = request.app.state.post_processor
    rag_pipeline = getattr(request.app.state, "rag_pipeline", None)

    # 1. Ambil record lama
    old_row = await doc_gen_repo.get(gen_id)
    if not old_row:
        raise HTTPException(status_code=404, detail="Record not found")

    source_text = old_row.get("source_text")
    partial_tor = old_row.get("tor_content")
    if not source_text:
        raise HTTPException(status_code=400, detail="generate.source_unavailable")
    if not partial_tor:
        raise HTTPException(status_code=400, detail="generate.continue_unavailable")

    # 2. Buat session baru agar proses continue tidak numpuk
    session_id = f"doc-{uuid.uuid4().hex[:8]}"
    filename = old_row["filename"]
    style_id = old_row.get("style_id")

    if style_id:
        try:
            active_style = style_manager.get_style(style_id)
        except StyleNotFoundError:
            active_style = style_manager.get_active_style()
    else:
        active_style = style_manager.get_active_style()

    await doc_gen_repo.create(
        gen_id=session_id,
        filename=filename,
        file_size=old_row["file_size"],
        context=old_row.get("context", ""),
        style_id=getattr(active_style, 'id', style_id),
        style_name=getattr(active_style, 'name', None),
    )
    await doc_gen_repo.update_source_text(session_id, source_text)

    async def event_stream():
        new_text = ""
        cancelled = False
        try:
            yield sse_event("status", {"msg": "Continuing document...", "session_id": session_id})
            if await request.is_disconnected():
                cancelled = True
                return

            rag_examples = None
            if rag_pipeline:
                try:
                    query = source_text[:200]
                    rag_examples = await rag_pipeline.retrieve(query, top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")

            format_spec = active_style.to_prompt_spec()
            prompt = GeminiPromptBuilder.build_continue(
                document_text=source_text,
                partial_tor=partial_tor,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )

            yield sse_event("status", {"msg": "Generating TOR..."})
            async for chunk in gemini.generate_stream(prompt):
                if await request.is_disconnected():
                    cancelled = True
                    break
                new_text += chunk
                yield sse_event("token", {"t": chunk})

            if cancelled:
                return

            combined_text = partial_tor + "\n" + new_text
            processed = post_processor.process(combined_text, style=active_style)
            
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
            
            # Hapus yang parsial agar bersih
            await doc_gen_repo.delete(gen_id)

            yield sse_event("done", {
                "session_id": session_id,
                "metadata": tor_metadata,
            })

        except GeminiTimeoutError as e:
            await doc_gen_repo.update_failed(session_id, f"Timeout: {e}")
            yield sse_event("error", {"msg": f"Generation timeout ({e})"})
        except asyncio.CancelledError:
            cancelled = True
        except GeneratorExit:
            cancelled = True
        except Exception as e:
            if type(e).__name__ == "ClientDisconnect":
                cancelled = True
            else:
                await doc_gen_repo.update_failed(session_id, str(e)[:500])
                yield sse_event("error", {"msg": str(e)[:300]})
        finally:
            if cancelled:
                try:
                    combined_partial = partial_tor + ("\n" + new_text if new_text else "")
                    msg = f"Cancelled by user. Partial continue: {len(combined_partial)} chars"
                    await doc_gen_repo.update_failed(session_id, msg, partial_content=combined_partial)
                except Exception:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )

