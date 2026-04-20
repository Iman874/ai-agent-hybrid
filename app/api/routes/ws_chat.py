"""WebSocket endpoint for streaming chat."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("ai-agent-hybrid.ws")

router = APIRouter()


@router.websocket("/ws/chat/{session_id}")
async def ws_chat(websocket: WebSocket, session_id: str | None = None):
    """WebSocket endpoint for streaming chat responses."""
    await websocket.accept()
    if session_id == "null":
        session_id = None
    logger.info(f"WS connected: session={session_id}")

    # Get services from app state
    app = websocket.app
    from app.services.stream_service import StreamService

    stream_service = StreamService(
        chat_service=app.state.chat_service,
        decision_engine=app.state.decision_engine,
    )

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") == "message":
                user_text = data.get("text", "")
                if not user_text.strip():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Pesan tidak boleh kosong.",
                    })
                    continue

                async for event in stream_service.stream_message(
                    session_id=session_id,
                    message=user_text,
                ):
                    msg = {"type": event.type}

                    if event.type in ("thinking_token", "token"):
                        msg["t"] = event.token
                    elif event.type == "done":
                        msg["data"] = event.response
                        # Update session_id if new session was created
                        if event.response and event.response.get("session_id"):
                            session_id = event.response["session_id"]
                    elif event.type == "error":
                        msg["error"] = event.error

                    await websocket.send_json(msg)

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WS error: {e}")
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except Exception:
            pass
