# Task 09 — SSE Tool Events

## Deskripsi

Menambahkan event types baru untuk tool calling ke SSE streaming endpoint. Frontend perlu tahu secara real-time ketika AI mulai memanggil tool, hasil eksekusinya, dan jika terjadi error. Tiga event baru ditambahkan: `tool_start`, `tool_result`, dan `tool_error`.

---

## Tujuan Teknis

- Frontend bisa menampilkan indikator real-time saat AI menggunakan tool
- Tiga event baru: `tool_start`, `tool_result`, `tool_error`
- Format event konsisten dengan SSE infrastructure yang sudah ada (`app/utils/sse.py`)
- Tool events muncul di antara event lainnya (status, thinking, token, done)
- Multiple tool calls dalam satu turn menghasilkan multiple events

---

## Scope

### Termasuk

- Modifikasi `app/services/stream_service.py`:
  - Update class `StreamEvent` — tambah tipe event untuk tool:
    ```python
    @dataclass
    class StreamEvent:
        type: str  # "tool_start" | "tool_result" | "tool_error" | ...
        response: dict | None = None
        token: str = ""
        error: str = ""
        tool: str = ""         # NEW — nama tool
        args: dict | None = None  # NEW — arguments tool
        status: str = ""       # NEW — "success" | "error"
        result_count: int = 0  # NEW — jumlah hasil
    ```

- Modifikasi `app/api/routes/hybrid.py`:
  - Update `hybrid_stream_endpoint()` — tambah handler untuk event type tool:
    ```python
    elif event.type == "tool_start":
        yield sse_event("tool_start", {
            "tool": event.tool,
            "args": event.args or {},
        })
    elif event.type == "tool_result":
        yield sse_event("tool_result", {
            "tool": event.tool,
            "status": event.status,
            "result_count": event.result_count,
        })
    elif event.type == "tool_error":
        yield sse_event("tool_error", {
            "tool": event.tool,
            "error": event.error,
        })
    ```

- Format SSE events:
  ```
  data: {"type": "tool_start", "tool": "web_search", "args": {"query": "AI Indonesia 2025", "max_results": 5}}
  
  data: {"type": "tool_result", "tool": "web_search", "status": "success", "result_count": 5}
  
  data: {"type": "tool_error", "tool": "web_search", "error": "Search API timeout"}
  ```

- Handle edge cases:
  - Multiple tool calls → multiple `tool_start` + `tool_result` berurutan
  - Tool gagal → `tool_error` bukan `tool_result`
  - Client disconnect di tengah tool execution → tetap aman (disconnect detection sudah ada)

### Tidak Termasuk

- Frontend component untuk tool indicator (Task 14)
- ChatStore update untuk tool events (Task 15)
- Logic tool calling itu sendiri (Task 04, 08)

---

## Langkah Implementasi

### Langkah 1: Update `StreamEvent` di `stream_service.py`

```python
# Di app/services/stream_service.py
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StreamEvent:
    """Event dalam streaming response.

    Attributes:
        type: Tipe event (status, token, thinking, done, error, tool_start, tool_result, tool_error).
        response: Data response untuk event type "status" dan "done".
        token: Token text untuk event type "token" dan "thinking_token".
        error: Pesan error untuk event type "error".
        tool: Nama tool untuk event type tool_*.
        args: Arguments tool untuk event type "tool_start".
        status: Status tool ("success" | "error") untuk event type "tool_result".
        result_count: Jumlah hasil tool untuk event type "tool_result".
    """
    type: str
    response: dict | None = None
    token: str = ""
    error: str = ""
    tool: str = ""
    args: dict[str, Any] | None = None
    status: str = ""
    result_count: int = 0
```

### Langkah 2: Update `hybrid_stream_endpoint()` di `hybrid.py`

```python
# Di app/api/routes/hybrid.py
# Di dalam event_generator() — tambah case untuk tool events

async def event_generator():
    try:
        async for event in chat_service.process_message_stream(
            session_id=body.session_id,
            message=body.message,
            chat_mode=body.options.chat_mode if body.options else "local",
            think=body.options.think if body.options else True,
            model_preference=body.options.model_preference if body.options else None,
            images=body.images,
            tools_enabled=body.options.tools_enabled if body.options else True,
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
            elif event.type == "tool_start":  # NEW
                yield sse_event("tool_start", {
                    "tool": event.tool,
                    "args": event.args or {},
                })
            elif event.type == "tool_result":  # NEW
                yield sse_event("tool_result", {
                    "tool": event.tool,
                    "status": event.status,
                    "result_count": event.result_count,
                })
            elif event.type == "tool_error":  # NEW
                yield sse_event("tool_error", {
                    "tool": event.tool,
                    "error": event.error,
                })
            elif event.type == "done":
                done_payload = dict(event.response or {})
                done_payload.pop("type", None)
                yield sse_event("done", done_payload)
            elif event.type == "error":
                yield sse_event("error", {"msg": event.error})

    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield sse_event("error", {"msg": str(e)})
```

### Langkah 3: Validasi

Test dengan curl atau script Python:

```python
import httpx
import json


async def test():
    """Test SSE tool events."""
    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/hybrid/stream",
            json={
                "session_id": None,
                "message": "Cari berita AI terbaru di Indonesia",
                "options": {
                    "chat_mode": "local",
                    "tools_enabled": True,
                },
            },
        ) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(f"Event: {data['type']}")
                    if data["type"] == "tool_start":
                        print(f"  → Tool: {data['tool']}, Args: {data['args']}")
                    elif data["type"] == "tool_result":
                        print(f"  → Result: {data['status']}, Count: {data['result_count']}")
                    elif data["type"] == "tool_error":
                        print(f"  → Error: {data['error']}")
                    elif data["type"] == "done":
                        print("  → Stream complete!")
                        break
```

---

## Output yang Diharapkan

- `hybrid_stream_endpoint()` bisa mengirim `tool_start`, `tool_result`, `tool_error` events
- Format SSE konsisten dengan event types yang sudah ada
- `StreamEvent` mendukung field untuk tool events
- Frontend bisa menerima dan memproses tool events

---

## Dependencies

- **Task 08 (ChatService Update)** — stream events dari ChatService

---

## Acceptance Criteria

### Functional
- [ ] `tool_start` event terkirim dengan field `tool` dan `args`
- [ ] `tool_result` event terkirim dengan field `tool`, `status`, `result_count`
- [ ] `tool_error` event terkirim dengan field `tool` dan `error`
- [ ] Multiple tool calls dalam satu turn menghasilkan multiple events
- [ ] Tool events tidak mengganggu event types lain (token, thinking, done)
- [ ] Client disconnect tetap terdeteksi dengan benar

### Edge Cases
- [ ] Tool dipanggil 3x → 3 pasang tool_start + tool_result
- [ ] Tool gagal → tool_error bukan tool_result
- [ ] Tool sukses dengan 0 hasil → tool_result dengan result_count=0
- [ ] Tidak ada tool call → tidak ada tool events

---

## Estimasi

**Low** (~1 jam)

| Aktivitas | Durasi |
|-----------|--------|
| Update StreamEvent dataclass | 15 menit |
| Update hybrid_stream_endpoint | 30 menit |
| Validasi & testing | 15 menit |
