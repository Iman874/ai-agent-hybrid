# Task 02: API Endpoint — Session List

> **Status**: [ ] Belum Dikerjakan
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 01 (SessionManager.list_all() harus sudah ada)

## 1. Deskripsi

Menambahkan endpoint `GET /api/v1/sessions` yang mengembalikan daftar session, urut dari terbaru. Endpoint ini dibutuhkan oleh frontend untuk menampilkan dropdown riwayat dan modal dialog.

## 2. Tujuan Teknis

- Endpoint `GET /sessions` berfungsi dan teregistrasi di router
- Response model `SessionListItem` terdefinisi dengan tipe yang benar
- Frontend bisa fetch daftar session via HTTP

## 3. Scope

**Yang dikerjakan:**
- Response model baru `SessionListItem` di `app/models/responses.py`
- Endpoint `GET /sessions` di `app/api/routes/session.py` (extend file existing)
- Expose `session_mgr` ke `app.state` (jika belum)

**Yang tidak dikerjakan:**
- Frontend (task03-05)
- Paginasi (di luar scope MVP)

## 4. Langkah Implementasi

### 4.1 Tambah Response Model

- [ ] Tambahkan class `SessionListItem` di `app/models/responses.py`:

```python
class SessionListItem(BaseModel):
    id: str
    title: str | None = None
    state: str
    turn_count: int
    created_at: str
    updated_at: str
    has_tor: bool
```

### 4.2 Expose `session_mgr` ke `app.state`

- [ ] Cek `app/main.py` apakah `session_mgr` sudah di-expose ke `app.state`:

Saat ini (line 37): `session_mgr = SessionManager(...)` → variabel lokal.
Mirip dengan bug `tor_cache` yang kita fix di beta 0.1.10, `session_mgr` hanya di-inject ke ChatService/GenerateService tapi **tidak langsung di `app.state`**.

- [ ] Tambahkan di `app/main.py` (setelah line 37):

```python
app.state.session_mgr = session_mgr  # expose untuk route session list
```

### 4.3 Tambah Endpoint di `session.py`

- [ ] Extend file `app/api/routes/session.py` — tambahkan endpoint `GET /sessions`:

```python
from app.models.responses import SessionDetailResponse, SessionListItem


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
```

**Catatan**: Import `SessionDetailResponse` sudah ada di file. Cukup tambahkan `SessionListItem` ke import yang sudah ada.

### 4.4 Verifikasi di Swagger

- [ ] Start server dan buka `http://localhost:8000/docs`
- [ ] Pastikan endpoint `GET /api/v1/sessions` muncul di bawah tag "Session"
- [ ] Test via Swagger → harus return array (bisa kosong jika belum ada session)

## 5. Output yang Diharapkan

```bash
curl http://localhost:8000/api/v1/sessions?limit=5
```

```json
[
  {
    "id": "abc-123-xxx",
    "title": "Workshop Penerapan AI...",
    "state": "COMPLETED",
    "turn_count": 8,
    "created_at": "2026-04-19T10:30:00",
    "updated_at": "2026-04-19T11:45:00",
    "has_tor": true
  },
  {
    "id": "def-456-xxx",
    "title": "Pengadaan Server Dat...",
    "state": "CHATTING",
    "turn_count": 3,
    "created_at": "2026-04-18T14:20:00",
    "updated_at": "2026-04-18T14:35:00",
    "has_tor": false
  }
]
```

## 6. Acceptance Criteria

- [ ] `GET /api/v1/sessions` return HTTP 200 dengan array body.
- [ ] Response mengandung semua fields: `id`, `title`, `state`, `turn_count`, `created_at`, `updated_at`, `has_tor`.
- [ ] Default limit = 50. `?limit=5` hanya return maksimal 5.
- [ ] Session diurutkan dari `updated_at` terbaru.
- [ ] Endpoint muncul di Swagger docs (`/docs`) di bawah tag "Session".
- [ ] `app.state.session_mgr` bisa diakses dari route tanpa error.
