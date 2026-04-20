# streamlit_app/state.py
"""Session state initialization and management."""

import streamlit as st
from config import THEME_FILE


def init_session_state():
    """Initialize semua session state keys dengan default values.
    
    Dipanggil sekali di app.py sebelum render apapun.
    """
    defaults = {
        "session_id": None,
        "messages": [],
        "current_state": {
            "status": "NEW",
            "turn_count": 0,
            "completeness_score": 0.0,
            "filled_fields": [],
            "missing_fields": [],
        },
        "tor_document": None,
        "escalation_info": None,
        "direct_tor": None,
        "doc_tor": None,
        "doc_session_id": None,
        "chat_mode": "local",
        "thinking_mode": True,
        "app_theme": _load_theme_pref(),
        "app_language": "id",
        "is_viewing_history": False,
        "history_session": None,
        "session_list": [],
        "active_tool": "chat",            # "chat" | "generate_doc"
        "active_model_id": None,          # e.g. "gemma4:e2b"
        "_loading_session_id": None,      # anti-flicker guard
        "_settings_section": "umum",      # "umum" | "format_tor" | "lanjutan"
        # UI action guard + perf (Beta 0.1.15)
        "_ui_action_seq": 0,
        "_ui_last_action": None,
        "_ui_busy": False,
        "_perf_enabled": False,
        "_perf_samples": [],
        "_theme_applied_once": False,
        "_theme_last_mode": None,
        # TOR export local cache (Beta 0.1.15)
        "_tor_export_cache": {},
        # Document style selection (Beta 0.1.12)
        "doc_style_mode": "active",        # "active" | "choose" | "auto_detect"
        "doc_selected_style_id": None,     # ID style spesifik jika dipilih
        "doc_detected_style": None,        # dict: hasil extraction dari AI
        "doc_awaiting_confirm": False,     # True = menunggu user confirm style
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session():
    """Reset chat session tanpa menghapus theme/mode preferences."""
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW",
        "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [],
        "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None
    st.session_state.doc_session_id = None
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None
    st.session_state._loading_session_id = None
    st.session_state.active_tool = "chat"  # Reset to default tool
    st.session_state._ui_busy = False
    st.session_state._ui_last_action = None
    st.session_state._tor_export_cache = {}
    # Reset doc style selection
    st.session_state.doc_style_mode = "active"
    st.session_state.doc_selected_style_id = None
    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False


def next_ui_action_id(action_name: str) -> str:
    """Generate ID action unik berbasis sequence counter."""
    seq = int(st.session_state.get("_ui_action_seq", 0)) + 1
    st.session_state._ui_action_seq = seq
    return f"{action_name}:{seq}"


def should_process_action(action_id: str) -> bool:
    """Return True jika action belum diproses sebelumnya."""
    return action_id != st.session_state.get("_ui_last_action")


def begin_ui_action(action_id: str) -> bool:
    """Start UI action jika guard meloloskan; return False jika ditolak."""
    if st.session_state.get("_ui_busy", False):
        return False
    if not should_process_action(action_id):
        return False
    st.session_state._ui_busy = True
    return True


def end_ui_action(action_id: str) -> None:
    """Mark UI action selesai dan lepas busy lock."""
    st.session_state._ui_last_action = action_id
    st.session_state._ui_busy = False


def record_perf_sample(name: str, ms: float) -> None:
    """Record perf sample ringkas ke session state saat perf mode aktif."""
    if not st.session_state.get("_perf_enabled", False):
        return

    samples: list[dict[str, str | float]] = st.session_state.get("_perf_samples", [])
    samples.append({"name": name, "ms": round(float(ms), 2)})
    if len(samples) > 200:
        samples = samples[-200:]
    st.session_state._perf_samples = samples


def load_history_session(session_data: dict):
    """Load session lama ke mode read-only.

    Args:
        session_data: Dict berisi session detail dari API
    """
    st.session_state.is_viewing_history = True
    st.session_state.history_session = session_data


def back_to_active():
    """Kembali dari history view ke session aktif saat ini."""
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None


def _load_theme_pref() -> str:
    """Baca pilihan theme dari file. Default: 'system'."""
    if THEME_FILE.exists():
        val = THEME_FILE.read_text().strip()
        if val in ("system", "dark", "light"):
            return val
    return "system"
