"""SSE (Server-Sent Events) formatting utility."""

import json


def sse_event(event_type: str, data: dict | None = None) -> str:
    """Format pesan SSE.

    Setiap event WAJIB punya field 'type'.
    Format output: data: {json}\n\n

    Args:
        event_type: Tipe event (status, token, done, error).
        data: Data tambahan yang akan di-merge ke payload.

    Returns:
        String SSE siap kirim.

    Contoh:
        >>> sse_event("token", {"t": "Hello"})
        'data: {"type": "token", "t": "Hello"}\\n\\n'
    """
    payload: dict = {"type": event_type}
    if data:
        payload.update(data)
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
