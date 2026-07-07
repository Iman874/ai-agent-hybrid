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
    Generate dokumen TOR via AI provider.

    - **session_id**: ID session dari chat engine
    - **mode**: `standard` (data lengkap) atau `escalation` (data parsial)
    - **generator**: `auto` | `gemini` | `ollama` (default: auto)
    - **force_regenerate**: `true` untuk bypass cache
    """
    generate_service = request.app.state.generate_service

    try:
        result = await generate_service.generate_tor(
            session_id=body.session_id,
            mode=body.mode,
            generator=body.generator,
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
    except Exception as e:
        from app.utils.errors import (
            NoProviderAvailableError, OllamaConnectionError, OllamaTimeoutError,
            ZenAPIError, ZenTimeoutError,
        )
        if isinstance(e, (
            NoProviderAvailableError, OllamaConnectionError, OllamaTimeoutError,
            ZenAPIError, ZenTimeoutError,
        )):
            return JSONResponse(
                status_code=503,
                content={"error": {"code": getattr(e, 'code', 'E999'), "message": str(e)}}
            )
        raise

    # Build response message
    if result.cached:
        message = "TOR served from cache."
    elif result.tor_document.metadata.mode == "escalation":
        message = "TOR has been generated based on available information. Sections marked [ASSUMPTION] can be adjusted."
    else:
        message = "TOR successfully generated based on the information you provided."

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
    Mendukung multi-provider: Gemini (cloud) dan Ollama (local).
    """
    generate_service = request.app.state.generate_service
    session_mgr = request.app.state.session_mgr
    gemini = request.app.state.gemini_provider
    ollama = request.app.state.ollama_generator
    zen = request.app.state.zen_provider
    cost_ctrl = generate_service.cost_ctrl
    post_processor = request.app.state.post_processor
    tor_cache = request.app.state.tor_cache
    style_manager = request.app.state.style_manager
    rag_pipeline = request.app.state.rag_pipeline

    async def event_stream():
        full_text = ""
        cancelled = False
        start_time = time.monotonic()
        provider_name = "gemini"  # default
        last_ping_time = time.monotonic()

        async def _maybe_ping():
            """Send keepalive ping every 15s to prevent proxy timeout."""
            nonlocal last_ping_time
            now = time.monotonic()
            if now - last_ping_time >= 15:
                last_ping_time = now
                yield sse_event("ping", {"ts": now})

        try:
            # Guard state
            session_check = await session_mgr.get(body.session_id)
            if session_check.state == "GENERATING":
                yield sse_event("error", {
                    "msg": "This session is already generating. Please wait until it finishes."
                })
                return

            if session_check.state == "COMPLETED" and session_check.generated_tor:
                yield sse_event("error", {
                    "msg": "TOR was already generated. Use a new session to regenerate."
                })
                return

            # Phase 1: Load session data
            if await request.is_disconnected():
                cancelled = True
                return
            async for ping in _maybe_ping():
                yield ping
            yield sse_event("status", {"msg": "Loading chat session data..."})

            session = await session_mgr.get(body.session_id)
            data = session.extracted_data
            history = await session_mgr.get_chat_history(body.session_id)

            # Completeness threshold is not enforced for generation.

            # Phase 1b: Resolve provider
            provider_name = await generate_service._resolve_provider(
                body.session_id, body.generator, body.mode
            )
            logger.info(
                f"Chat stream resolved provider: {provider_name} "
                f"(requested: {body.generator})"
            )

            # Phase 2: RAG + Style + Prompt
            if await request.is_disconnected():
                cancelled = True
                return
            async for ping in _maybe_ping():
                yield ping
            yield sse_event("status", {"msg": "Building AI instructions..."})

            rag_examples = None
            if rag_pipeline and data.judul:
                try:
                    rag_examples = await rag_pipeline.retrieve(data.judul, top_k=2)
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without: {e}")

            active_style = style_manager.get_active_style()
            format_spec = active_style.to_prompt_spec()

            # Pilih prompt builder sesuai provider
            if provider_name == "gemini":
                from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history as gemini_fmt
                prompt_builder = GeminiPromptBuilder()
                if body.mode == "standard":
                    prompt = prompt_builder.build_standard(
                        data=data, rag_examples=rag_examples, format_spec=format_spec,
                    )
                else:
                    formatted_history = gemini_fmt(history)
                    prompt = prompt_builder.build_escalation(
                        chat_history=formatted_history, partial_data=data,
                        rag_examples=rag_examples, format_spec=format_spec,
                    )
            else:
                from app.core.ollama_prompt_builder import OllamaPromptBuilder, format_chat_history as ollama_fmt
                prompt_builder = OllamaPromptBuilder()
                if body.mode == "standard":
                    prompt = prompt_builder.build_standard(
                        data=data, rag_examples=rag_examples, format_spec=format_spec,
                    )
                else:
                    formatted_history = ollama_fmt(history)
                    prompt = prompt_builder.build_escalation(
                        chat_history=formatted_history, partial_data=data,
                        rag_examples=rag_examples, format_spec=format_spec,
                    )

            # Phase 3: Stream dari provider yang dipilih
            if await request.is_disconnected():
                cancelled = True
                return
            yield sse_event("status", {"msg": "Generating TOR document..."})

            await session_mgr.update(body.session_id, state="GENERATING")
            logger.info(
                f"Generate chat stream started: session={body.session_id}, "
                f"mode={body.mode}, provider={provider_name}"
            )

            if provider_name == "gemini":
                async for chunk in gemini.generate_stream(prompt):
                    if await request.is_disconnected():
                        cancelled = True
                        break
                    full_text += chunk
                    yield sse_event("token", {"t": chunk})
                    async for ping in _maybe_ping():
                        yield ping
            elif provider_name == "zen":
                try:
                    async for chunk in zen.generate_stream(prompt):
                        if await request.is_disconnected():
                            cancelled = True
                            break
                        full_text += chunk
                        yield sse_event("token", {"t": chunk})
                        async for ping in _maybe_ping():
                            yield ping
                except Exception as e:
                    logger.warning(
                        f"Zen stream failed, falling back to non-stream: {e}"
                    )
                    raw_text = await zen.generate(prompt)
                    if await request.is_disconnected():
                        cancelled = True
                    else:
                        full_text += raw_text
                        yield sse_event("token", {"t": raw_text})
            else:
                try:
                    async for chunk in ollama.generate_stream(prompt):
                        if await request.is_disconnected():
                            cancelled = True
                            break
                        full_text += chunk
                        yield sse_event("token", {"t": chunk})
                        async for ping in _maybe_ping():
                            yield ping
                except Exception as e:
                    logger.warning(
                        f"Ollama stream failed, falling back to non-stream: {e}"
                    )
                    # Fallback: non-streaming generate (single chunk)
                    raw_text = await ollama.generate(prompt)
                    if await request.is_disconnected():
                        cancelled = True
                    else:
                        full_text += raw_text
                        yield sse_event("token", {"t": raw_text})

            if cancelled:
                return

            # Phase 4: Post-processing
            yield sse_event("status", {"msg": "Formatting document..."})
            processed = post_processor.process(full_text, style=active_style)

            # Phase 5: Persist ke DB & Cache
            duration_ms = int((time.monotonic() - start_time) * 1000)

            if provider_name == "gemini":
                model_name = gemini.model_name
            elif provider_name == "zen":
                model_name = zen.model
            else:
                model_name = ollama.model
            tor_metadata = {
                "generated_by": model_name,
                "generator": provider_name,
                "mode": body.mode,
                "word_count": processed.word_count,
                "has_assumptions": processed.has_assumptions,
            }

            tor_doc = TORDocument(
                content=processed.content,
                metadata=TORMetadata(
                    generated_by=model_name,
                    generator=provider_name,
                    mode=body.mode,
                    word_count=processed.word_count,
                    generation_time_ms=duration_ms,
                    has_assumptions=processed.has_assumptions,
                    prompt_tokens=0,
                    completion_tokens=0,
                ),
            )

            # Cache untuk semua provider (agar export bisa bekerja)
            await tor_cache.store(body.session_id, tor_doc)
            if provider_name == "gemini":
                await cost_ctrl.log_call(
                    body.session_id, model_name, body.mode,
                    0, 0, duration_ms, success=True,
                )

            await session_mgr.update(
                body.session_id,
                state="COMPLETED",
                generated_tor=processed.content,
                gemini_calls_count=(
                    session.gemini_calls_count + 1
                    if provider_name == "gemini"
                    else session.gemini_calls_count
                ),
            )

            # Phase 6: Done event
            yield sse_event("done", {
                "session_id": body.session_id,
                "metadata": tor_metadata,
            })

        except Exception as e:
            logger.error(f"Chat stream generate error ({provider_name}): {e}")
            await session_mgr.update(body.session_id, state="READY")
            yield sse_event("error", {"msg": str(e)[:300]})

        finally:
            if cancelled:
                logger.info(
                    f"Generate chat stream cancelled: session={body.session_id}, "
                    f"provider={provider_name}, partial={len(full_text)} chars"
                )
                # Save partial content to session even if client disconnected
                if full_text:
                    try:
                        processed = post_processor.process(full_text, style=active_style)
                        await session_mgr.update(
                            body.session_id,
                            state="COMPLETED",
                            generated_tor=processed.content,
                        )
                        logger.info(
                            f"Partial TOR saved for cancelled session: "
                            f"{body.session_id}, {processed.word_count} words"
                        )
                    except Exception as save_err:
                        logger.warning(
                            f"Failed to save partial TOR for cancelled session: {save_err}"
                        )
                        await session_mgr.update(body.session_id, state="READY")
                else:
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
