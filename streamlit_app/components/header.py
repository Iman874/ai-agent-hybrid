# streamlit_app/components/header.py
"""Header area - title bar only."""

import streamlit as st
from utils.icons import mi
from utils.i18n import tr


def render_header():
    """Render header: hanya tampil di mode obrolan."""
    tool = st.session_state.get("active_tool", "chat")
    if tool != "chat":
        return

    icon = mi("smart_toy", 20, "var(--color-primary)")
    st.markdown(
        f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
        f"{icon} {tr('header.title', 'Generator TOR')}"
        f'</h3>',
        unsafe_allow_html=True,
    )
