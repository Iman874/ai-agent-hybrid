# streamlit_app/app.py
"""
TOR Generator — AI Agent Hybrid
Entry point untuk Streamlit UI.

Jalankan: streamlit run streamlit_app/app.py --server.port 8501
"""

import streamlit as st
from config import PAGE_CONFIG
from state import init_session_state
from theme import apply_saved_theme
from styles.loader import inject_styles
from components.sidebar import render_sidebar
from components.header import render_header
from components.chat import render_chat_tab
from components.form_document import render_document_tab


# ============================================
# BOOTSTRAP
# ============================================
st.set_page_config(**PAGE_CONFIG)
init_session_state()
apply_saved_theme()
inject_styles()


# ============================================
# LAYOUT
# ============================================
render_sidebar()
render_header()

tool = st.session_state.get("active_tool", "chat")
if tool == "chat":
    render_chat_tab()
elif tool == "generate_doc":
    render_document_tab()
