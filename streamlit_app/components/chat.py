# streamlit_app/components/chat.py
"""Chat tab — interactive TOR building via conversation."""

import streamlit as st
from utils.icons import mi
from api.client import send_message, handle_response
from components.tor_preview import render_tor_preview


def render_chat_tab():
    """Render tab Chat: empty state / messages / TOR preview / input."""

    # Empty state
    if not st.session_state.messages and not st.session_state.tor_document:
        _render_empty_state()

    # Message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # TOR Preview (jika sudah di-generate)
    if st.session_state.tor_document:
        render_tor_preview(
            st.session_state.tor_document,
            st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    # Chat input
    if prompt := st.chat_input("Tanyakan apa saja..."):
        _handle_user_input(prompt)


def _render_empty_state():
    """Render empty state dengan Material Icon besar dan pesan terarah."""
    icon = mi("forum", 64, "var(--color-text-subtle)")
    st.markdown(
        f'''
        <div class="empty-state">
            {icon}
            <h3>Ceritakan kebutuhan TOR Anda</h3>
            <p>
                Mulai chat untuk menyusun Term of Reference<br>
                dengan bantuan AI secara interaktif.
            </p>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def _handle_user_input(prompt: str):
    """Process user input: append message, call API, handle response."""
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API
    with st.spinner("AI sedang memproses permintaan..."):
        data = send_message(st.session_state.session_id, prompt)

    # Handle response
    if handle_response(data):
        st.rerun()
