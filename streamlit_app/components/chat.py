# streamlit_app/components/chat.py
"""Chat tab — interactive TOR building via conversation."""

from time import perf_counter

import streamlit as st
from utils.icons import mi
from utils.i18n import tr
from utils.notify import notify
from state import (
    back_to_active,
    begin_ui_action,
    end_ui_action,
    record_perf_sample,
)
from api.client import send_message, handle_response
from components.tor_preview import render_tor_preview


def render_chat_tab():
    """Render tab Chat: empty state / messages / TOR preview / input."""

    # === HISTORY VIEW MODE ===
    if st.session_state.is_viewing_history:
        _render_history_view()
        return

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
            session_id=st.session_state.session_id,
            escalation_info=st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    # Chat input
    if prompt := st.chat_input(tr("chat.input_placeholder", "Tanyakan apa saja...")):
        _handle_user_input(prompt)


def _render_empty_state():
    """Render empty state dengan Material Icon besar dan pesan terarah."""
    icon = mi("forum", 64, "var(--color-text-subtle)")
    st.markdown(
        f'''
        <div class="empty-state">
            {icon}
            <h3>{tr("chat.empty_title", "Ceritakan kebutuhan TOR Anda")}</h3>
            <p>
                {tr("chat.empty_desc", "Mulai chat untuk menyusun Term of Reference dengan bantuan AI secara interaktif.")}
            </p>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def _handle_user_input(prompt: str):
    """Process user input: append message, call API, handle response."""
    action_id = _build_chat_action_id(prompt)
    if not begin_ui_action(action_id):
        notify(tr("chat.processing_previous", "Permintaan sebelumnya masih diproses."), "info", method="inline")
        return

    t0 = perf_counter()

    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Call API
        with st.spinner(tr("chat.processing_spinner", "AI sedang memproses permintaan...")):
            data = send_message(st.session_state.session_id, prompt)

        # Handle response
        should_rerun = handle_response(data)
    finally:
        end_ui_action(action_id)
        record_perf_sample("chat_send", (perf_counter() - t0) * 1000)

    if should_rerun:
        st.rerun()


def _build_chat_action_id(prompt: str) -> str:
    """Build deterministic action ID untuk dedupe submit chat."""
    session_id = st.session_state.get("session_id") or "new"
    turn_count = st.session_state.get("current_state", {}).get("turn_count", 0)
    normalized_prompt = " ".join(prompt.strip().split())
    return f"chat:send:{session_id}:{turn_count}:{normalized_prompt}"


def _render_history_view():
    """Tampilkan session lama dalam mode read-only."""
    hist = st.session_state.history_session

    if not hist:
        notify(tr("chat.history_not_available", "Data session tidak tersedia."), "warning", method="inline")
        if st.button(f"← {tr('chat.back', 'Kembali')}"):
            back_to_active()
            st.rerun()
        return

    # --- Banner Info ---
    session_title = hist.get("extracted_data", {}).get("judul") or f"{tr('chat.history_prefix', 'Session')} {hist['id'][:8]}..."
    session_state = hist.get("state", "—")
    session_turns = hist.get("turn_count", 0)

    notify(
        tr(
            "chat.history_banner",
            "Arsip session: {title}. Status: {status} · {turns} Turn. Mode read-only, tidak bisa mengirim pesan baru.",
            title=session_title,
            status=session_state,
            turns=session_turns,
        ),
        "info",
        icon="history",
        method="inline",
    )

    # --- Tombol Kembali ---
    if st.button(f"← {tr('chat.back_to_active', 'Kembali ke Obrolan Aktif')}", type="primary"):
        back_to_active()
        st.rerun()

    st.divider()

    # --- Render Chat History (read-only) ---
    chat_history = hist.get("chat_history", [])

    if not chat_history:
        st.caption(tr("chat.history_empty", "_Session ini tidak memiliki riwayat chat._"))
    else:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)

    # --- TOR Preview (jika ada) ---
    generated_tor = hist.get("generated_tor")
    if generated_tor:
        st.divider()
        # Bangun tor dict yang kompatibel dengan render_tor_preview()
        tor_dict = {
            "content": generated_tor,
            "metadata": hist.get("metadata", {}),
        }
        render_tor_preview(
            tor=tor_dict,
            session_id=hist["id"],
            key_suffix="_history",
        )
        
        # --- Fallback: Download langsung dari data history (tanpa API export) ---
        st.divider()
        st.caption(tr("chat.fallback_caption", "Jika tombol export di atas error, gunakan fallback di bawah:"))
        fb1, fb2 = st.columns(2)
        with fb1:
            st.download_button(
                tr("chat.fallback_download_md", "Download .md (fallback)"),
                data=generated_tor,
                file_name=f"tor_history_{hist['id'][:8]}.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_history_md_fb",
            )
