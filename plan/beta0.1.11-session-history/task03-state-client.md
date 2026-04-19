# Task 03: Frontend State Management + API Client

> **Status**: [ ] Belum Dikerjakan
> **Estimasi**: Low (30 menit – 1 jam)
> **Dependency**: Task 02 (endpoint harus sudah ada)

## 1. Deskripsi

Menambahkan state keys baru di `state.py` untuk mendukung History View Mode, dan menambahkan fungsi API client di `client.py` untuk fetch daftar session dan detail session.

## 2. Tujuan Teknis

- Streamlit session state mendukung `is_viewing_history`, `history_session`, `session_list`
- API client bisa memanggil `GET /sessions` dan `GET /session/{id}`
- Fungsi helper `load_history_session()` dan `back_to_active()` tersedia

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/state.py` — tambah state keys + fungsi helper
- `streamlit_app/api/client.py` — tambah 2 fungsi

**Yang tidak dikerjakan:**
- Sidebar UI (task04)
- Chat history view (task05)

## 4. Langkah Implementasi

### 4.1 Update `state.py` — Tambah State Keys

- [ ] Tambahkan 3 key baru di dict `defaults` dalam fungsi `init_session_state()`:

```python
defaults = {
    # ... key existing ...
    "session_id": None,
    "messages": [],
    # ... dll ...

    # BARU: Session History
    "is_viewing_history": False,        # True = sedang lihat arsip
    "history_session": None,            # dict: session detail + chat history
    "session_list": [],                 # cache list session dari API
}
```

### 4.2 Update `state.py` — Tambah Fungsi Helper

- [ ] Tambahkan 2 fungsi baru di akhir `state.py`:

```python
def load_history_session(session_data: dict):
    """Load session lama ke mode read-only.

    Args:
        session_data: Dict berisi session detail dari API
                      (keys: id, chat_history, generated_tor, state, dll)
    """
    st.session_state.is_viewing_history = True
    st.session_state.history_session = session_data


def back_to_active():
    """Kembali dari history view ke session aktif saat ini."""
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None
```

### 4.3 Update `state.py` — Tambah Reset untuk History Keys

- [ ] Tambahkan reset keys di fungsi `reset_session()`:

```python
def reset_session():
    """Reset chat session tanpa menghapus theme/mode preferences."""
    # ... existing reset code ...
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None

    # BARU: reset history view
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None
```

### 4.4 Tambah Fungsi di `client.py`

- [ ] Tambahkan 2 fungsi baru di `streamlit_app/api/client.py` (sebelum section `# --- Export API Endpoints ---`):

```python
# --- Session History API ---

def fetch_session_list(limit: int = 10) -> list[dict]:
    """Ambil daftar session terbaru dari backend.

    Args:
        limit: Jumlah maksimal session yang diambil.

    Returns:
        list[dict]: Daftar session, atau [] jika gagal.
    """
    try:
        resp = requests.get(
            f"{API_URL}/sessions",
            params={"limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Gagal memuat riwayat session: {e}")
        return []


def fetch_session_detail(session_id: str) -> dict | None:
    """Ambil detail session + chat history untuk history view.

    Args:
        session_id: ID session yang ingin dilihat.

    Returns:
        dict: Session detail lengkap, atau None jika gagal.
    """
    try:
        resp = requests.get(
            f"{API_URL}/session/{session_id}",
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            st.error("Session tidak ditemukan.")
        else:
            st.error(f"Gagal memuat session: HTTP {e.response.status_code}")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None
```

## 5. Output yang Diharapkan

```python
# Di Streamlit:
from api.client import fetch_session_list, fetch_session_detail
from state import load_history_session, back_to_active

# Fetch daftar session
sessions = fetch_session_list(limit=10)
# [{"id": "abc", "title": "Workshop...", "state": "COMPLETED", ...}, ...]

# Load session tertentu ke history view
detail = fetch_session_detail("abc-123")
# {"id": "abc-123", "chat_history": [...], "generated_tor": "...", ...}
load_history_session(detail)
# st.session_state.is_viewing_history == True
# st.session_state.history_session == detail

# Kembali ke session aktif
back_to_active()
# st.session_state.is_viewing_history == False
```

## 6. Acceptance Criteria

- [ ] `st.session_state` memiliki key `is_viewing_history`, `history_session`, `session_list` setelah `init_session_state()`.
- [ ] `fetch_session_list(10)` mengembalikan list (bisa kosong) tanpa crash.
- [ ] `fetch_session_detail(valid_id)` mengembalikan dict dengan key `chat_history`.
- [ ] `fetch_session_detail(invalid_id)` mengembalikan `None` dan menampilkan error.
- [ ] `load_history_session(data)` mengset `is_viewing_history = True`.
- [ ] `back_to_active()` mengset `is_viewing_history = False` dan `history_session = None`.
- [ ] `reset_session()` juga mereset `is_viewing_history` dan `history_session`.
