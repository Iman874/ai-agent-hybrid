# Task 19: SSE Endpoint `POST /hybrid/stream`

## Deskripsi

Membuat SSE endpoint baru di FastAPI untuk chat streaming. Endpoint menerima JSON body dan mengembalikan `StreamingResponse` dengan event-event SSE yang konsisten.

## Tujuan Teknis

- Endpoint `POST /hybrid/stream` → `StreamingResponse(media_type="text/event-stream")`
- Format SSE identik dengan generate stream: `data: {"type": "..."}\n\n`
- Client disconnect detection
- Error standardization

## Scope

**Dikerjakan:**
- Tambah SSE endpoint di `app/api/routes/hybrid.py`
- Client disconnect detection
- Reuse `sse_event()` helper dari generate module
- Register route di app

**Tidak dikerjakan:**
- Frontend (Task 20-21)
- Provider logic (Task 17)
- ChatService logic (Task 18)

## Langkah Implementasi

### Step 1: Tambah endpoint di `hybrid.py`

File: `app/api/routes/hybrid.py`

```python
from fastapi import Request
from fastapi.responses import StreamingResponse
from app.models.api import HybridRequest
from app.services.stream_service import StreamEvent

@router.post("/hybrid/stream")
async def hybrid_stream_endpoint(request: Request, body: HybridRequest):
    """
    SSE streaming endpoint untuk hybrid chat.
    Mengembalikan token real-time dari LLM.
    """
    chat_service = request.app.state.chat_service
    
    async def event_generator():
        try:
            async for event in chat_service.process_message_stream(
                session_id=body.session_id,
                message=body.message,
                chat_mode=body.options.chat_mode if body.options else "local",
                think=body.options.think if body.options else True,
            ):
                # Check client disconnect
                if await request.is_disconnected():
                    logger.info("Client disconnected during stream")
                    break
                
                # Convert StreamEvent ke SSE format
                if event.type == "status":
                    yield sse_event({"type": "status", "msg": "Memproses...", "session_id": event.response.get("session_id") if event.response else None})
                
                elif event.type == "thinking_start":
                    yield sse_event({"type": "thinking_start"})
                
                elif event.type == "thinking_token":
                    yield sse_event({"type": "thinking", "t": event.token})
                
                elif event.type == "thinking_end":
                    yield sse_event({"type": "thinking_end"})
                
                elif event.type == "token":
                    yield sse_event({"type": "token", "t": event.token})
                
                elif event.type == "done":
                    yield sse_event({"type": "done", **event.response})
                
                elif event.type == "error":
                    yield sse_event({"type": "error", "msg": event.error})

        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield sse_event({"type": "error", "msg": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

### Step 2: Import/reuse `sse_event()` helper

Cek apakah `sse_event()` sudah ada di codebase (dari beta 0.2.5 generate module). Jika sudah ada:

```python
from app.api.routes.generate_doc import sse_event  # atau dari utility shared
```

Jika belum ada sebagai shared utility, buat di `app/utils/sse.py`:

```python
import json

def sse_event(data: dict) -> str:
    """Format data sebagai SSE event string."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
```

### Step 3: Register endpoint

Pastikan route sudah terdaftar di `app/main.py` atau `app/api/__init__.py`. Endpoint `hybrid` router kemungkinan sudah terdaftar — endpoint baru `/hybrid/stream` otomatis ikut.

### Step 4: Test dengan curl

```bash
curl -X POST http://localhost:8000/hybrid/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Saya ingin membuat TOR untuk proyek AI"}' \
  --no-buffer
```

Expected output:
```
data: {"type": "status", "msg": "Memproses...", "session_id": "abc-123"}

data: {"type": "token", "t": "Baik"}

data: {"type": "token", "t": ", saya"}

data: {"type": "token", "t": " akan"}

data: {"type": "done", "session_id": "abc-123", "message": "...", "state": {...}}

```

## Output yang Diharapkan

- Endpoint `/hybrid/stream` berfungsi
- SSE events mengalir real-time saat LLM generate token
- Client disconnect tidak crash server
- Error di-wrap sebagai SSE error event

## Dependencies

- Task 17: Provider `chat_stream()` ready
- Task 18: `ChatService.process_message_stream()` ready

## Acceptance Criteria

- [ ] `POST /hybrid/stream` endpoint ada dan berfungsi
- [ ] Format SSE: `data: {"type": "..."}\n\n`
- [ ] Event types: `status`, `thinking_start`, `thinking`, `thinking_end`, `token`, `done`, `error`
- [ ] Client disconnect handled (server tidak crash)
- [ ] Error di-wrap sebagai SSE event (bukan HTTP 500)
- [ ] `curl` test menunjukkan token mengalir real-time
- [ ] `uvicorn` reload tanpa error

## Estimasi

Medium (1-2 jam)
