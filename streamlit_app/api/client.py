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
    opts["think"] = st.session_state.get("thinking_mode", True)
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

# --- Styles API Endpoints ---

def get_styles() -> list[dict]:
    """Mengambil list format styles dari backend."""
    try:
        resp = requests.get(f"{API_URL}/styles", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

def get_active_style() -> dict | None:
    """Mengambil definisi style yang saat ini aktif."""
    try:
        resp = requests.get(f"{API_URL}/styles/active", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None

def set_active_style(style_id: str) -> bool:
    """Atur default style terpilih."""
    try:
        resp = requests.post(f"{API_URL}/styles/{style_id}/activate", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

def update_style(style_id: str, updates: dict) -> dict:
    """Merubah form properties dict payload custom template style."""
    try:
        resp = requests.put(f"{API_URL}/styles/{style_id}", json=updates, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}

def delete_style(style_id: str) -> dict:
    """Hapus json format storage by id."""
    try:
        resp = requests.delete(f"{API_URL}/styles/{style_id}", timeout=5)
        resp.raise_for_status()
        return {"status": "ok"}
    except requests.HTTPError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}

def duplicate_style(style_id: str, new_name: str) -> dict:
    """Kloning template yg sudah ada."""
    try:
        resp = requests.post(f"{API_URL}/styles/{style_id}/duplicate", json={"new_name": new_name}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}

def extract_style(file_bytes: bytes, filename: str) -> dict:
    """Upload dan parse extraction text AI."""
    try:
        resp = requests.post(
            f"{API_URL}/styles/extract",
            files={"file": (filename, file_bytes)},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        return {"error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"error": str(e)}

