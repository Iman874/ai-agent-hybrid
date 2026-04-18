from fastapi import APIRouter, Request

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, SessionState

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest, request: Request):
    """
    Kirim pesan ke Chat Engine. Auto-create session baru jika session_id null.

    Body:
    - session_id (optional): UUID session yang sudah ada
    - message (required): Pesan user (1-5000 chars)
    """
    chat_service = request.app.state.chat_service

    result = await chat_service.process_message(
        session_id=body.session_id,
        message=body.message,
        rag_context=None,  # RAG belum ada di beta0.1.0
    )

    return ChatResponse(
        session_id=result.session_id,
        type="chat",
        message=result.message,
        state=SessionState(
            status=result.status,
            turn_count=result.completeness_score,  # Nanti diganti kalo fix di turn_count, sepertinya di task description ada typo
            completeness_score=result.completeness_score,
            filled_fields=result.extracted_data.filled_fields(),
            missing_fields=result.missing_fields,
        ),
        extracted_data=result.extracted_data,
    )
