# Task 1: SSE Utility Helper

## 1. Judul Task
Buat modul utility `sse_event()` untuk memformat Server-Sent Events.

## 2. Deskripsi
Semua SSE event yang dikirim dari backend ke frontend harus menggunakan format yang konsisten. Utility ini menjadi satu-satunya cara memformat event — memastikan setiap event SELALU punya field `type`.

## 3. Tujuan Teknis
- File `app/utils/sse.py` berisi fungsi `sse_event()`
- Format output: `data: {"type":"<event_type>", ...}\n\n`
- Dapat diimport dari seluruh codebase

## 4. Scope
### Yang dikerjakan
- Buat file `app/utils/sse.py`

### Yang tidak dikerjakan
- Tidak membuat endpoint (task 3)
- Tidak mengubah Gemini provider (task 2)

## 5. Langkah Implementasi

### Step 1: Buat `app/utils/sse.py`

```python
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
```

### Step 2: Verifikasi manual

```python
from app.utils.sse import sse_event

print(sse_event("status", {"msg": "Memproses..."}))
# data: {"type": "status", "msg": "Memproses..."}\n\n

print(sse_event("token", {"t": "Hello "}))
# data: {"type": "token", "t": "Hello "}\n\n

print(sse_event("done", {"session_id": "doc-abc", "metadata": {}}))
# data: {"type": "done", "session_id": "doc-abc", "metadata": {}}\n\n

print(sse_event("error", {"msg": "Timeout"}))
# data: {"type": "error", "msg": "Timeout"}\n\n
```

## 6. Output yang Diharapkan

```
data: {"type": "status", "msg": "Memproses dokumen..."}\n\n
data: {"type": "token", "t": "# TOR "}\n\n
data: {"type": "done", "session_id": "doc-abc123", "metadata": {"word_count": 1200}}\n\n
data: {"type": "error", "msg": "Timeout saat generate"}\n\n
```

## 7. Dependencies
Tidak ada (task pertama).

## 8. Acceptance Criteria
- [ ] File `app/utils/sse.py` ada
- [ ] `sse_event("token", {"t": "x"})` → `'data: {"type": "token", "t": "x"}\n\n'`
- [ ] `sse_event("error", {"msg": "err"})` → `'data: {"type": "error", "msg": "err"}\n\n'`
- [ ] `ensure_ascii=False` agar karakter Indonesia tidak di-escape
- [ ] Backend startup tanpa error import

## 9. Estimasi
**Low** (~15 menit)
