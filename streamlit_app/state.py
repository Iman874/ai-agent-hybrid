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
        "chat_mode": "local",
        "thinking_mode": True,
        "app_theme": _load_theme_pref(),
        "is_viewing_history": False,
        "history_session": None,
        "session_list": [],
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
    st.session_state.is_viewing_history = False
    st.session_state.history_session = None
    # Reset doc style selection
    st.session_state.doc_style_mode = "active"
    st.session_state.doc_selected_style_id = None
    st.session_state.doc_detected_style = None
    st.session_state.doc_awaiting_confirm = False


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
