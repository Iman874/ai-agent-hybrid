import logging
import time
import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.models.generate import GenerateRequest, GenerateResponse, TORDocument, TORMetadata
from app.utils.errors import (
    RateLimitError, GeminiAPIError, GeminiTimeoutError, InsufficientDataError
)
from app.utils.sse import sse_event
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history

logger = logging.getLogger("ai-agent-hybrid.api.generate")

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_tor(request: Request, body: GenerateRequest):
    """
    Generate dokumen TOR via Gemini API.

    - **session_id**: ID session dari chat engine
    - **mode**: `standard` (data lengkap) atau `escalation` (data parsial)
    - **force_regenerate**: `true` untuk bypass cache
    """
    generate_service = request.app.state.generate_service

    try:
        result = await generate_service.generate_tor(
            session_id=body.session_id,
            mode=body.mode,
            force_regenerate=body.force_regenerate,
        )
    except InsufficientDataError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )
    except RateLimitError as e:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": e.code, "message": e.message, "retry_after_seconds": 120}}
        )
    except GeminiTimeoutError as e:
        return JSONResponse(
            status_code=504,
            content={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )
    except GeminiAPIError as e:
        return JSONResponse(
            status_code=502,
            content={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )

    # Build response message
    if result.cached:
        message = "TOR disajikan dari cache."
    elif result.tor_document.metadata.mode == "escalation":
        message = "TOR telah dibuat berdasarkan informasi yang tersedia. Bagian yang ditandai [ASUMSI] dapat disesuaikan."
    else:
        message = "TOR berhasil dibuat berdasarkan informasi yang Anda berikan."

    return GenerateResponse(
        session_id=result.session_id,
        message=message,
        tor_document=result.tor_document,
        cached=result.cached,
    )


@router.post("/generate/chat/stream")
async def generate_tor_from_chat_stream(request: Request, body: GenerateRequest):
    """
    Streaming TOR generation dari sesi chat.
    Menggunakan SSE untuk men-stream token Gemini secara real-time.
    """
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
            # Guard state
            session_check = await session_mgr.get(body.session_id)
            if session_check.state == "GENERATING":
                yield sse_event("error", {
                    "msg": "Sesi ini sedang dalam proses generate. Tunggu hingga selesai."
                })
                return

            if session_check.state == "COMPLETED" and session_check.generated_tor:
                yield sse_event("error", {
                    "msg": "TOR sudah dibuat sebelumnya. Gunakan session baru untuk membuat ulang."
                })
                return

            # Phase 1: Load session data
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Memeriksa data sesi chat..."})

            session = await session_mgr.get(body.session_id)
            data = session.extracted_data
            history = await session_mgr.get_chat_history(body.session_id)

            if body.mode == "standard" and session.completeness_score < 0.3:
                yield sse_event("error", {
                    "msg": f"Data belum cukup (skor: {session.completeness_score:.0%}). "
                           "Lanjutkan chat untuk melengkapi informasi."
                })
                return

            # Phase 2: RAG + Style + Prompt
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Menyusun instruksi untuk AI..."})

            rag_examples = None
            if rag_pipeline and data.judul:
                try:
                    rag_examples = await rag_pipeline.retrieve(data.judul, top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without: {e}")

            active_style = style_manager.get_active_style()
            format_spec = active_style.to_prompt_spec()

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

            # Phase 3: Stream Gemini
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Mulai membuat dokumen TOR..."})

            await session_mgr.update(body.session_id, state="GENERATING")
            logger.info(f"Generate chat stream started: session={body.session_id}, mode={body.mode}")

            async for chunk in gemini.generate_stream(prompt):
                if await request.is_disconnected():
                    cancelled = True
                    break
                full_text += chunk
                yield sse_event("token", {"t": chunk})

            if cancelled:
                return

            # Phase 4: Post-processing
            yield sse_event("status", {"msg": "Merapikan format dokumen..."})
            processed = post_processor.process(full_text, style=active_style)

            # Phase 5: Persist ke DB & Cache
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

            # Phase 6: Done event
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
            if cancelled:
                logger.info(
                    f"Generate chat stream cancelled: session={body.session_id}, "
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
