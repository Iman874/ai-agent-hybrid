import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.api import HybridRequest, HybridAPIResponse, SessionState
from app.models.routing import RoutingResult
from app.core.capability_resolver import ModelCapabilityResolver
from app.utils.sse import sse_event

logger = logging.getLogger("ai-agent-hybrid.api.hybrid")

router = APIRouter()

_resolver = ModelCapabilityResolver()


def _validate_image_support(body: HybridRequest, settings) -> None:
    """Reject images jika model aktif tidak support vision."""
    if not body.images:
        return

    if body.options and body.options.chat_mode == "gemini":
        active_model = settings.gemini_model
        provider = "google"
    else:
        active_model = settings.ollama_chat_model
        provider = "ollama"

    caps = _resolver.resolve(active_model, provider)
    if not caps.supports_image_input:
        raise HTTPException(
            status_code=400,
            detail="This model does not support image input. "
                   "Select a vision model (like Gemini or llava) to send images.",
        )


@router.post("/hybrid", response_model=HybridAPIResponse)
async def hybrid_endpoint(request: Request, body: HybridRequest):
    """
    Main endpoint. Kirim pesan, sistem otomatis routing antara
    chat (local LLM) dan generate (Gemini).
    """
    _validate_image_support(body, request.app.state.settings)

    decision_engine = request.app.state.decision_engine

    result = await decision_engine.route(
        session_id=body.session_id,
        message=body.message,
        options=body.options,
        images=body.images,
    )

    return _convert_to_api_response(result)


@router.post("/hybrid/stream")
async def hybrid_stream_endpoint(request: Request, body: HybridRequest):
    """SSE endpoint untuk streaming chat token real-time."""
    _validate_image_support(body, request.app.state.settings)

    chat_service = request.app.state.chat_service

    async def event_generator():
        try:
            async for event in chat_service.process_message_stream(
                session_id=body.session_id,
                message=body.message,
                chat_mode=body.options.chat_mode if body.options else "local",
                think=body.options.think if body.options else True,
                images=body.images,
            ):
                if await request.is_disconnected():
                    logger.info("Client disconnected during /hybrid/stream")
                    break

                if event.type == "status":
                    session_id = event.response.get("session_id") if event.response else None
                    yield sse_event("status", {
                        "msg": "Processing...",
                        "session_id": session_id,
                    })
                elif event.type == "thinking_start":
                    yield sse_event("thinking_start")
                elif event.type == "thinking_token":
                    yield sse_event("thinking", {"t": event.token})
                elif event.type == "thinking_end":
                    yield sse_event("thinking_end")
                elif event.type == "token":
                    yield sse_event("token", {"t": event.token})
                elif event.type == "done":
                    done_payload = dict(event.response or {})
                    done_payload.pop("type", None)
                    yield sse_event("done", done_payload)
                elif event.type == "error":
                    yield sse_event("error", {"msg": event.error})

        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield sse_event("error", {"msg": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _convert_to_api_response(result: RoutingResult) -> HybridAPIResponse:
    """Convert internal RoutingResult ke API response."""
    if result.generate_response:
        # Generate response (standard atau escalation)
        chat = result.chat_response
        return HybridAPIResponse(
            session_id=result.session_id,
            type="generate",
            message=chat.message if chat else "TOR successfully generated.",
            state=SessionState(
                status="COMPLETED",
                turn_count=0,
                completeness_score=chat.completeness_score if chat else 1.0,
                filled_fields=chat.extracted_data.filled_fields() if chat else [],
                missing_fields=chat.missing_fields if chat else [],
            ),
            extracted_data=chat.extracted_data if chat else None,
            tor_document=result.generate_response.tor_document,
            escalation_info=result.escalation_info,
            cached=result.generate_response.cached,
        )
    else:
        # Chat response
        chat = result.chat_response
        return HybridAPIResponse(
            session_id=result.session_id,
            type="chat",
            message=chat.message,
            state=SessionState(
                status=chat.status,
                turn_count=0,
                completeness_score=chat.completeness_score,
                filled_fields=chat.extracted_data.filled_fields(),
                missing_fields=chat.missing_fields,
            ),
            extracted_data=chat.extracted_data,
        )
