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
from components.form_direct import render_direct_tab
from components.form_document import render_document_tab
from components.format_tab import render_format_tab


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

tab_chat, tab_direct, tab_doc, tab_format = st.tabs([
    "Chat",
    "Gemini Direct",
    "Dari Dokumen",
    "Format TOR",
])

with tab_chat:
    render_chat_tab()

with tab_direct:
    render_direct_tab()

with tab_doc:
    render_document_tab()

with tab_format:
    render_format_tab()
