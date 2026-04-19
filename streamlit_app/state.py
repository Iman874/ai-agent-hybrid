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


def _load_theme_pref() -> str:
    """Baca pilihan theme dari file. Default: 'system'."""
    if THEME_FILE.exists():
        val = THEME_FILE.read_text().strip()
        if val in ("system", "dark", "light"):
            return val
    return "system"
