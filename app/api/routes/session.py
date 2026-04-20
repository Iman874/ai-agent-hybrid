from fastapi import APIRouter, Request, HTTPException

from app.models.responses import SessionDetailResponse, SessionListItem

router = APIRouter()


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(
    request: Request,
    limit: int = 50,
):
    """List semua session, urut dari terbaru.

    - **limit**: Jumlah maksimal session yang dikembalikan (default 50).
    """
    session_mgr = request.app.state.session_mgr
    sessions = await session_mgr.list_all(limit=limit)

    return [
        SessionListItem(
            id=s["id"],
            title=s["title"],
            state=s["state"],
            turn_count=s["turn_count"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            has_tor=s["has_tor"],
        )
        for s in sessions
    ]



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


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, request: Request):
    """Hapus session beserta semua message-nya."""
    session_mgr = request.app.state.session_mgr
    success = await session_mgr.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sesi tidak ditemukan")
    return {"status": "deleted", "session_id": session_id}
