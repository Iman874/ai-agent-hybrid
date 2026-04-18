from fastapi import APIRouter, Request

from app.models.responses import SessionDetailResponse

router = APIRouter()


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, request: Request):
    """Get detail session beserta chat history."""
    chat_service = request.app.state.chat_service

    session = await chat_service.get_session(session_id)
    history = await chat_service.get_chat_history(session_id)

    return SessionDetailResponse(
        id=session.id,
        created_at=str(session.created_at),
        updated_at=str(session.updated_at),
        state=session.state,
        turn_count=session.turn_count,
        completeness_score=session.completeness_score,
        extracted_data=session.extracted_data,
        chat_history=[
            {
                "role": msg.role,
                "content": msg.content,
                "parsed_status": msg.parsed_status,
                "timestamp": str(msg.timestamp),
            }
            for msg in history
        ],
        generated_tor=session.generated_tor,
        metadata={
            "gemini_calls_count": session.gemini_calls_count,
            "total_tokens_local": session.total_tokens_local,
            "total_tokens_gemini": session.total_tokens_gemini,
        },
    )
