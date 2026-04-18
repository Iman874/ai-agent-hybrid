import logging
from fastapi import APIRouter, Request
from app.models.api import HybridRequest, HybridAPIResponse, SessionState
from app.models.routing import RoutingResult

logger = logging.getLogger("ai-agent-hybrid.api.hybrid")

router = APIRouter()


@router.post("/hybrid", response_model=HybridAPIResponse)
async def hybrid_endpoint(request: Request, body: HybridRequest):
    """
    Main endpoint. Kirim pesan, sistem otomatis routing antara
    chat (local LLM) dan generate (Gemini).
    """
    decision_engine = request.app.state.decision_engine

    result = await decision_engine.route(
        session_id=body.session_id,
        message=body.message,
        options=body.options,
    )

    return _convert_to_api_response(result)


def _convert_to_api_response(result: RoutingResult) -> HybridAPIResponse:
    """Convert internal RoutingResult ke API response."""
    if result.generate_response:
        # Generate response (standard atau escalation)
        chat = result.chat_response
        return HybridAPIResponse(
            session_id=result.session_id,
            type="generate",
            message=chat.message if chat else "TOR berhasil dibuat.",
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
