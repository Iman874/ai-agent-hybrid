import logging
import uuid
import json
import asyncio
import time
from typing import Literal
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from app.core.document_parser import DocumentParser
from app.core.gemini_prompt_builder import GeminiPromptBuilder
from app.core.ollama_prompt_builder import OllamaPromptBuilder
from app.core.style_manager import StyleNotFoundError
from app.models.generate import TORDocument, TORMetadata, GenerateResponse
from app.utils.errors import DocumentParseError, GeminiTimeoutError, NoProviderAvailableError
from app.utils.sse import sse_event

logger = logging.getLogger("ai-agent-hybrid.api.generate_doc")

router = APIRouter()


async def _resolve_doc_provider(
    gemini_provider,
    ollama_provider,
    generator: str,
) -> str:
    """Resolve provider untuk document generation.

    Args:
        gemini_provider: Gemini provider instance.
        ollama_provider: Ollama generator provider instance.
        generator: "auto" | "gemini" | "ollama".

    Returns:
        str: Nama provider terpilih ("gemini" | "ollama").

    Raises:
        NoProviderAvailableError: Semua provider tidak tersedia.
    """
    if generator == "gemini":
        if await gemini_provider.is_available():
            return "gemini"
        elif await ollama_provider.is_available():
            logger.warning("Gemini unavailable, falling back to Ollama")
            return "ollama"
        else:
            raise NoProviderAvailableError(
                "Gemini unavailable (API key missing or invalid), "
                "Ollama unavailable (not running or model not found)"
            )

    elif generator == "ollama":
        if await ollama_provider.is_available():
            return "ollama"
        elif await gemini_provider.is_available():
            logger.warning("Ollama unavailable, falling back to Gemini")
            return "gemini"
        else:
            raise NoProviderAvailableError(
                "Ollama unavailable (not running or model not found), "
                "Gemini unavailable (API key missing or invalid)"
            )

    else:  # "auto"
        # Auto: prefer Ollama (local, gratis) jika tersedia, fallback ke Gemini
        if await ollama_provider.is_available():
            return "ollama"
        elif await gemini_provider.is_available():
            return "gemini"

        raise NoProviderAvailableError(
            "No generator provider available. "
            "Ensure Ollama is running or Gemini API key is configured."
        )


def _truncate_document_text(
    text: str,
    provider_name: str,
    max_chars: int = 6000,
) -> str:
    """Truncate document text agar muat di context window model.

    Ollama dengan num_ctx=8192 butuh ruang untuk prompt + format spec.
    Jika teks terlalu panjang, ambil bagian awal (paling relevan) + akhir.
    """
    if len(text) <= max_chars:
        return text

    logger.warning(
        f"Document text too long ({len(text)} chars), truncating to {max_chars} chars "
        f"for provider={provider_name}"
    )

    # Ambil 70% dari awal, 30% dari akhir
    head_ratio = 0.7
    head_chars = int(max_chars * head_ratio)
    tail_chars = max_chars - head_chars

    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars > 0 else ""

    truncated = f"{head}\n\n[... TRUNCATED: {len(text) - max_chars} characters removed ...]\n\n{tail}"
    return truncated[:max_chars]


@router.post("/generate/from-document", response_model=GenerateResponse)
async def generate_from_document(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
    style_id: str | None = Form(None, description="ID style TOR spesifik (default=aktif)"),
    generator: Literal["auto", "gemini", "ollama"] = Form("auto", description="Provider AI: auto, gemini, atau ollama"),
    model_preference: str | None = Form(None, description="Preferred model id (optional)"),
):
    """
    Generate TOR dari dokumen yang diupload.

    - **file**: Dokumen sumber (PDF, TXT, MD, DOCX). Maks 20MB.
    - **context**: Konteks tambahan, misal "Buat TOR lanjutan 2026".
    - **generator**: Provider AI — "auto" | "gemini" | "ollama" (default: auto).
    - **model_preference**: ID model yang dipilih user (optional).
    """
    gemini = request.app.state.gemini_provider
    ollama = request.app.state.ollama_generator
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

        # Step 4b: Truncate untuk Ollama agar tidak overflow context window
        provider_name = await _resolve_doc_provider(gemini, ollama, generator)
        document_text = _truncate_document_text(document_text, provider_name)

        model_override = None
        if provider_name == "ollama" and model_preference:
            model_override = model_preference
            if not await ollama.is_model_available(model_override):
                raise HTTPException(
                    status_code=400,
                    detail=f"Ollama model '{model_override}' tidak tersedia.",
                )

        # Log model yang dipakai
        model_to_use = model_override or (gemini.model_name if provider_name == "gemini" else ollama.model)
        logger.info(f"Doc generate will use model: {model_to_use} (provider={provider_name}, override={model_override})")

        # Step 5: RAG (optional — retrieve style examples)
        rag_examples = None
        if rag_pipeline:
            try:
                query = document_text[:200]
                rag_examples = await rag_pipeline.retrieve(query, top_k=2)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        format_spec = active_style.to_prompt_spec()

        # Step 6: Resolve provider
        logger.info(f"Doc generate resolved provider: {provider_name} (requested: {generator})")

        # Step 7: Build prompt (pilih builder sesuai provider)
        if provider_name == "gemini":
            prompt = GeminiPromptBuilder.build_from_document(
                document_text=document_text,
                user_context=context,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )
        else:
            prompt = OllamaPromptBuilder.build_from_document(
                document_text=document_text,
                user_context=context,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )

        # Step 8: Call provider
        start_time = time.monotonic()

        if provider_name == "gemini":
            gemini_response = await gemini.generate(prompt)
            raw_text = gemini_response.text
            duration_ms = gemini_response.duration_ms
            prompt_tokens = gemini_response.prompt_tokens
            completion_tokens = gemini_response.completion_tokens
            model_name = gemini.model_name
        else:
            raw_text = await ollama.generate(prompt, model_override)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            prompt_tokens = 0
            completion_tokens = 0
            model_name = model_override or ollama.model

        # Step 9: Post-process
        processed = post_processor.process(raw_text, style=active_style)

        tor_doc = TORDocument(
            content=processed.content,
            metadata=TORMetadata(
                generated_by=model_name,
                generator=provider_name,
                mode="standard",
                word_count=processed.word_count,
                generation_time_ms=duration_ms,
                has_assumptions=processed.has_assumptions,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
        )

        # Step 10: Persist completed
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
            f"provider={provider_name}, model={model_name}, time={duration_ms}ms"
        )

        return GenerateResponse(
            session_id=session_id,
            message=f"TOR successfully generated from document '{filename}'.",
            tor_document=tor_doc,
            cached=False,
        )

    except Exception as e:
        # Step 11: Persist failure
        await doc_gen_repo.update_failed(session_id, str(e)[:500])
        raise


@router.post("/generate/from-document/stream")
async def generate_from_document_stream(
    request: Request,
    file: UploadFile = File(..., description="Dokumen sumber (PDF/TXT/MD/DOCX)"),
    context: str = Form("", description="Konteks tambahan dari user"),
    style_id: str | None = Form(None, description="ID style TOR spesifik (default=aktif)"),
    generator: Literal["auto", "gemini", "ollama"] = Form("auto", description="Provider AI: auto, gemini, atau ollama"),
    model_preference: str | None = Form(None, description="Preferred model id (optional)"),
):
    """Generate TOR dari dokumen — streaming via SSE.

    Event types:
    - status: {"type":"status","msg":"..."} — progress status
    - token: {"type":"token","t":"..."} — text chunk dari AI provider
    - done: {"type":"done","session_id":"...","metadata":{...}} — selesai
    - error: {"type":"error","msg":"..."} — error

    Mendukung multi-provider: Gemini (cloud) dan Ollama (local).
    Parameter `generator` menentukan provider: "auto" | "gemini" | "ollama".
    Parameter `model_preference` menentukan model spesifik (optional).
    """
    gemini = request.app.state.gemini_provider
    ollama = request.app.state.ollama_generator
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
        last_ping_time = 0
        model_to_use = None

        async def _maybe_ping():
            """Send keepalive ping every 15s to prevent proxy timeout."""
            nonlocal last_ping_time
            now = time.monotonic()
            if now - last_ping_time >= 15:
                last_ping_time = now
                yield sse_event("ping", {"ts": now})

        try:
            # Phase 1: Parse document
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Processing document...", "session_id": session_id})
            document_text = await DocumentParser.parse(file_bytes, filename)
            await doc_gen_repo.update_source_text(session_id, document_text)

            # Phase 1b: Resolve provider & truncate untuk Ollama
            provider_name = await _resolve_doc_provider(gemini, ollama, generator)
            document_text = _truncate_document_text(document_text, provider_name)
            logger.info(f"Doc stream resolved provider: {provider_name} (requested: {generator})")

            model_override = None
            if provider_name == "ollama" and model_preference:
                model_override = model_preference
                if not await ollama.is_model_available(model_override):
                    yield sse_event("error", {"msg": f"Ollama model '{model_override}' tidak tersedia."})
                    return

            # Log model yang dipakai
            model_to_use = model_override or (gemini.model_name if provider_name == "gemini" else ollama.model)
            logger.info(f"Doc stream will use model: {model_to_use} (provider={provider_name}, override={model_override})")

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

            # Phase 2c: Build prompt sesuai provider
            if provider_name == "gemini":
                prompt = GeminiPromptBuilder.build_from_document(
                    document_text=document_text,
                    user_context=context,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )
            else:
                prompt = OllamaPromptBuilder.build_from_document(
                    document_text=document_text,
                    user_context=context,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )

            # Phase 3: Stream dari provider yang dipilih
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Generating TOR..."})
            start_time = time.monotonic()
            # start timer for generation duration (used for metadata)
            start_time = time.monotonic()

            if provider_name == "gemini":
                async for chunk in gemini.generate_stream(prompt):
                    if await request.is_disconnected():
                        cancelled = True
                        break
                    full_text += chunk
                    yield sse_event("token", {"t": chunk})
                    async for _ in _maybe_ping():
                        yield _
            else:
                # Ollama: try streaming
                logger.info(f"Starting streaming generate for model: {model_to_use}")
                chunk_count = 0
                content_chunks = 0
                empty_chunks = 0
                try:
                    # Call generate_stream which returns an async generator
                    stream = ollama.generate_stream(prompt, model_override)
                    async for chunk in stream:
                        chunk_count += 1
                        
                        # Track chunks with content vs empty chunks
                        has_content = len(chunk) > 0
                        if has_content:
                            content_chunks += 1
                            empty_chunks = 0
                        
                        # Log progress (not just first 3)
                        if chunk_count <= 10 or chunk_count % 10 == 0 or has_content:
                            logger.debug(f"Chunk #{chunk_count}: len={len(chunk)}, has_content={has_content}")
                            if has_content:
                                logger.info(f"Content chunk #{content_chunks}: {chunk[:50]}...")
                            else:
                                logger.info(f"Empty chunk #{chunk_count} received while waiting for content")
                        
                        if await request.is_disconnected():
                            cancelled = True
                            logger.warning(f"Client disconnected at chunk #{chunk_count}")
                            break
                        
                        # Accumulate and yield content
                        if has_content:
                            full_text += chunk
                            yield sse_event("token", {"t": chunk})
                        else:
                            empty_chunks += 1
                            if empty_chunks == 1 or empty_chunks % 10 == 0:
                                yield sse_event(
                                    "status",
                                    {
                                        "msg": f"Generating TOR... received {chunk_count} chunks, waiting for first text token",
                                    },
                                )
                        
                        # Send keepalive every 15s (even for empty chunks to prevent timeout)
                        async for _ in _maybe_ping():
                            yield _
                    
                    logger.info(f"Streaming complete: total_chunks={chunk_count}, content_chunks={content_chunks}, total_text={len(full_text)} chars")
                except Exception as e:
                    logger.error(f"Ollama stream failed after {chunk_count} chunks ({content_chunks} with content): {type(e).__name__}: {e}", exc_info=True)
                    logger.info(f"Falling back to non-streaming mode")
                    raw_text = await ollama.generate(prompt, model_override)
                    if await request.is_disconnected():
                        cancelled = True
                    else:
                        full_text += raw_text
                        yield sse_event("token", {"t": raw_text})

            # Jika cancelled mid-stream, JANGAN post-process
            if cancelled:
                return

            # Phase 4: Post-process (hanya jika stream selesai lengkap)
            processed = post_processor.process(full_text, style=active_style)

            # Phase 5: Persist completed
            model_name = gemini.model_name if provider_name == "gemini" else (model_override or ollama.model)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            tor_metadata = {
                "generated_by": model_name,
                "generator": provider_name,
                "mode": "standard",
                "word_count": processed.word_count,
                "generation_time_ms": duration_ms,
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
                f"model={model_to_use}, provider={provider_name}, words={processed.word_count}, time={duration_ms}ms"
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
    ollama = request.app.state.ollama_generator
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

    # Truncate untuk Ollama
    provider_name = await _resolve_doc_provider(gemini, ollama, "auto")
    source_text = _truncate_document_text(source_text, provider_name)

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

            # Build prompt sesuai provider
            if provider_name == "gemini":
                prompt = GeminiPromptBuilder.build_from_document(
                    document_text=source_text,
                    user_context=context,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )
            else:
                prompt = OllamaPromptBuilder.build_from_document(
                    document_text=source_text,
                    user_context=context,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )

            yield sse_event("status", {"msg": "Generating TOR..."})

            if provider_name == "gemini":
                async for chunk in gemini.generate_stream(prompt):
                    if await request.is_disconnected():
                        cancelled = True
                        break
                    full_text += chunk
                    yield sse_event("token", {"t": chunk})
            else:
                try:
                    async for chunk in ollama.generate_stream(prompt):
                        if await request.is_disconnected():
                            cancelled = True
                            break
                        full_text += chunk
                        yield sse_event("token", {"t": chunk})
                except Exception as e:
                    logger.warning(f"Ollama stream failed, falling back to non-stream: {e}")
                    raw_text = await ollama.generate(prompt)
                    if await request.is_disconnected():
                        cancelled = True
                    else:
                        full_text += raw_text
                        yield sse_event("token", {"t": raw_text})

            if cancelled:
                return

            processed = post_processor.process(full_text, style=active_style)
            model_name = gemini.model_name if provider_name == "gemini" else ollama.model
            duration_ms = int((time.monotonic() - start_time) * 1000)
            tor_metadata = {
                "generated_by": model_name,
                "generator": provider_name,
                "mode": "standard",
                "word_count": processed.word_count,
                "generation_time_ms": duration_ms,
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
    ollama = request.app.state.ollama_generator
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

    # Truncate untuk Ollama
    provider_name = await _resolve_doc_provider(gemini, ollama, "auto")
    source_text = _truncate_document_text(source_text, provider_name)

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

            if provider_name == "gemini":
                prompt = GeminiPromptBuilder.build_continue(
                    document_text=source_text,
                    partial_tor=partial_tor,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )
            else:
                prompt = OllamaPromptBuilder.build_continue(
                    document_text=source_text,
                    partial_tor=partial_tor,
                    rag_examples=rag_examples,
                    format_spec=format_spec,
                )

            yield sse_event("status", {"msg": "Generating TOR..."})

            if provider_name == "gemini":
                async for chunk in gemini.generate_stream(prompt):
                    if await request.is_disconnected():
                        cancelled = True
                        break
                    new_text += chunk
                    yield sse_event("token", {"t": chunk})
            else:
                try:
                    async for chunk in ollama.generate_stream(prompt):
                        if await request.is_disconnected():
                            cancelled = True
                            break
                        new_text += chunk
                        yield sse_event("token", {"t": chunk})
                except Exception as e:
                    logger.warning(f"Ollama stream failed, falling back to non-stream: {e}")
                    raw_text = await ollama.generate(prompt)
                    if await request.is_disconnected():
                        cancelled = True
                    else:
                        new_text += raw_text
                        yield sse_event("token", {"t": raw_text})

            if cancelled:
                return

            combined_text = partial_tor + "\n" + new_text
            processed = post_processor.process(combined_text, style=active_style)
            
            model_name = gemini.model_name if provider_name == "gemini" else ollama.model
            tor_metadata = {
                "generated_by": model_name,
                "generator": provider_name,
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

