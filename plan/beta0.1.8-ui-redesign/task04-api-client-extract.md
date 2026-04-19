# Task 04: API Client Extract — `api/client.py`

## Status: 🔲 Pending

---

## 1. Judul Task

Extract semua HTTP API calls ke modul terpisah `api/client.py`.

## 2. Deskripsi

Pindahkan semua fungsi yang berkomunikasi dengan FastAPI backend dari
`streamlit_app.py` ke `api/client.py`. Ini termasuk: `send_message`,
`check_health`, `fetch_models`, `force_generate`, `generate_direct`,
`generate_from_document`, dan `handle_response`.

## 3. Tujuan Teknis

- Satu file bertanggung jawab atas semua API communication
- `requests` library hanya di-import di satu tempat
- Semua komponen cukup `from api.client import send_message` tanpa perlu
  tahu detail HTTP

## 4. Scope

**Yang dikerjakan:**
- `api/client.py` — 7 fungsi API
- Semua logic error handling per fungsi (ConnectionError, Timeout, HTTPError)

**Yang TIDAK dikerjakan:**
- UI rendering (itu di komponen)
- Session state mutation di `handle_response` (akan import dari `state.py` jika perlu)

## 5. Langkah Implementasi

### Step 1: Buat `api/client.py`

Extract dari `streamlit_app.py` lines 114-206:

```python
# streamlit_app/api/client.py
"""HTTP client for FastAPI backend communication."""

import requests
import streamlit as st
from config import API_URL


def send_message(
    session_id: str | None,
    message: str,
    options: dict | None = None,
) -> dict:
    """Kirim pesan ke hybrid endpoint.

    Args:
        session_id: ID session (None = buat baru)
        message: Pesan dari user
        options: Opsi tambahan (force_generate, chat_mode, dll)

    Returns:
        dict: Response JSON dari backend, atau {"error": "..."} jika gagal
    """
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    opts = options or {}
    opts["chat_mode"] = st.session_state.get("chat_mode", "local")
    payload["options"] = opts
    try:
        resp = requests.post(f"{API_URL}/hybrid", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi. Pastikan server berjalan di port 8000."}
    except requests.Timeout:
        return {"error": "Request timeout. LLM mungkin sedang sibuk, coba lagi."}
    except requests.HTTPError as e:
        try:
            return {"error": e.response.json().get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def check_health() -> dict:
    """Health check API backend.

    Returns:
        dict: {"status": "healthy"} atau {"status": "unreachable"}
    """
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.json()
    except Exception:
        return {"status": "unreachable"}


@st.cache_data(ttl=30)
def fetch_models() -> list[dict]:
    """Fetch daftar model tersedia dari backend.

    Returns:
        list[dict]: List model objects [{"id": "...", "type": "...", "status": "..."}]
    """
    try:
        resp = requests.get(f"{API_URL}/models", timeout=5)
        return resp.json().get("models", [])
    except Exception:
        return []


def force_generate(session_id: str) -> dict:
    """Force generate TOR dari session yang ada.

    Args:
        session_id: ID session aktif

    Returns:
        dict: Response dengan TOR document
    """
    return send_message(session_id, "generate", options={"force_generate": True})


def generate_direct(data: dict) -> dict:
    """Generate TOR langsung dari structured form data (tanpa chat).

    Args:
        data: dict dengan keys: judul, latar_belakang, tujuan, dll.

    Returns:
        dict: Response dengan TOR document
    """
    parts = []
    for key, label in [
        ("judul", "Judul kegiatan"),
        ("latar_belakang", "Latar belakang"),
        ("tujuan", "Tujuan"),
        ("ruang_lingkup", "Ruang lingkup"),
        ("output", "Output/deliverable"),
        ("timeline", "Timeline"),
        ("estimasi_biaya", "Estimasi biaya"),
    ]:
        if data.get(key):
            parts.append(f"{label}: {data[key]}")
    message = "Buatkan TOR dengan data berikut:\n" + "\n".join(parts)
    return send_message(None, message, options={"force_generate": True})


def generate_from_document(
    file_bytes: bytes,
    filename: str,
    context: str = "",
) -> dict:
    """Generate TOR dari uploaded document.

    Args:
        file_bytes: Binary content of uploaded file
        filename: Original filename
        context: Optional additional context

    Returns:
        dict: Response dengan TOR document
    """
    try:
        resp = requests.post(
            f"{API_URL}/generate/from-document",
            files={"file": (filename, file_bytes)},
            data={"context": context},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Backend tidak bisa dihubungi."}
    except requests.Timeout:
        return {"error": "Request timeout."}
    except requests.HTTPError as e:
        try:
            return {"error": e.response.json().get("error", {}).get("message", str(e))}
        except Exception:
            return {"error": f"HTTP Error: {e.response.status_code}"}


def handle_response(data: dict) -> bool:
    """Process API response dan update session state.

    Args:
        data: Response dict dari API

    Returns:
        bool: True jika response valid, False jika error
    """
    if "error" in data:
        st.error(f"❌ {data['error']}")
        return False
    st.session_state.session_id = data["session_id"]
    st.session_state.current_state = data["state"]
    st.session_state.messages.append({
        "role": "assistant",
        "content": data["message"],
    })
    if data.get("tor_document"):
        st.session_state.tor_document = data["tor_document"]
    if data.get("escalation_info"):
        st.session_state.escalation_info = data["escalation_info"]
    return True
```

### Step 2: Test import di `app.py`

```python
from api.client import check_health, fetch_models

health = check_health()
st.write(f"API: {health.get('status')}")

models = fetch_models()
st.write(f"Models: {len(models)}")
```

## 6. Output yang Diharapkan

```
streamlit_app/api/
├── __init__.py
└── client.py     (~140 lines — 7 fungsi)
```

## 7. Dependencies

- **Task 01** — folder `api/` harus ada, `config.py` harus ada (API_URL)

## 8. Acceptance Criteria

- [ ] `api/client.py` berisi 7 fungsi: send_message, check_health, fetch_models, force_generate, generate_direct, generate_from_document, handle_response
- [ ] `requests` hanya di-import di file ini
- [ ] Semua fungsi memiliki docstring lengkap
- [ ] Error handling per fungsi (ConnectionError, Timeout, HTTPError)
- [ ] `check_health()` dan `fetch_models()` bisa dipanggil dari `app.py` tanpa error
- [ ] `handle_response()` update `st.session_state` dengan benar

## 9. Estimasi

**Low** — Copy-paste dari monolit + tambah docstring.
