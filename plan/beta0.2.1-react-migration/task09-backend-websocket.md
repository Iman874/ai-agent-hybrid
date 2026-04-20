# Task 09: Backend WebSocket — Streaming Endpoint

## 1. Judul Task

Buat WebSocket endpoint di FastAPI untuk streaming chat responses

## 2. Deskripsi

Membuat endpoint `ws/chat/{session_id}` yang menerima pesan via WebSocket dan mengirim response token-by-token (streaming). Termasuk heartbeat, error handling, dan integrasi dengan decision engine.

## 3. Tujuan Teknis

- Endpoint WebSocket `/ws/chat/{session_id}`
- Streaming protokol: thinking_start → thinking_token → thinking_end → token → done
- Heartbeat ping/pong
- Error handling dengan graceful disconnect
- `stream_service.py` sebagai async generator wrapper

## 4. Scope

**Yang dikerjakan:**
- `app/api/routes/ws_chat.py` — WebSocket endpoint
- `app/services/stream_service.py` — streaming wrapper
- `app/api/router.py` — register WS route

**Yang tidak dikerjakan:**
- Frontend WS client (task 10)
- Modifikasi Ollama/Gemini provider internal (gunakan existing streaming jika ada)

## 5. Langkah Implementasi

### 5.1 `app/services/stream_service.py`

```python
"""Streaming service — wraps chat/decision engine into async event generator."""

import logging
import dataclasses
from typing import AsyncGenerator, Literal

logger = logging.getLogger("ai-agent-hybrid.stream")


@dataclasses.dataclass
class StreamEvent:
    type: Literal[
        "thinking_start", "thinking_token", "thinking_end",
        "token", "done", "error"
    ]
    token: str = ""
    response: dict | None = None
    error: str = ""


class StreamService:
    """Wraps chat_service.process_message into streaming events."""

    def __init__(self, chat_service, decision_engine):
        self.chat_service = chat_service
        self.decision_engine = decision_engine

    async def stream_message(
        self, session_id: str | None, message: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Process message and yield streaming events."""
        try:
            # Phase 1: Thinking
            yield StreamEvent(type="thinking_start")
            yield StreamEvent(type="thinking_token", token="Menganalisis pertanyaan...")

            # Phase 2: Process via decision engine (non-streaming for now)
            result = await self.decision_engine.route(
                session_id=session_id,
                message=message,
            )

            yield StreamEvent(type="thinking_end")

            # Phase 3: Stream response tokens
            response_text = ""
            if result.chat_response:
                response_text = result.chat_response.message
            elif result.generate_response:
                response_text = result.generate_response.tor_document.content if result.generate_response.tor_document else "TOR berhasil dibuat."

            # Simulate token streaming from full response
            words = response_text.split(" ")
            for word in words:
                yield StreamEvent(type="token", token=word + " ")

            # Phase 4: Done with full response data
            from app.api.routes.hybrid import _convert_to_api_response
            api_response = _convert_to_api_response(result)

            yield StreamEvent(
                type="done",
                response=api_response.model_dump(),
            )

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield StreamEvent(type="error", error=str(e))
```

### 5.2 `app/api/routes/ws_chat.py`

```python
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
```

### 5.3 Register di Router

```python
# app/api/router.py — tambah:
from app.api.routes import ws_chat

# Di atas api_router.include_router lines, tambah:
api_router.include_router(ws_chat.router, tags=["WebSocket"])
```

**Catatan**: WebSocket route harus di-register tanpa prefix `/api/v1` agar URL jadi `/ws/chat/{id}`. Alternatif: register langsung di `main.py`:

```python
# app/main.py — tambah setelah app.include_router(api_router):
from app.api.routes.ws_chat import router as ws_router
app.include_router(ws_router)
```

## 6. Output yang Diharapkan

WebSocket connection test:
```
> wscat -c ws://localhost:8000/ws/chat/null
Connected

> {"type": "message", "text": "Bantu buat TOR training"}
< {"type": "thinking_start"}
< {"type": "thinking_token", "t": "Menganalisis pertanyaan..."}
< {"type": "thinking_end"}
< {"type": "token", "t": "Baik, "}
< {"type": "token", "t": "saya "}
< {"type": "token", "t": "akan "}
< {"type": "token", "t": "membantu..."}
< {"type": "done", "data": {...}}
```

## 7. Dependencies

- Backend sudah running (decision_engine, chat_service sudah init)
- Tidak butuh task frontend manapun

## 8. Acceptance Criteria

- [ ] WebSocket connect ke `ws://localhost:8000/ws/chat/{id}` berhasil
- [ ] Kirim message → terima streaming events
- [ ] Heartbeat ping/pong berfungsi
- [ ] Error handling: pesan kosong → error event
- [ ] Session baru: session_id ter-update dari response
- [ ] Disconnect graceful tanpa crash server
- [ ] Server start tanpa error

## 9. Estimasi

High (2-3 jam)
