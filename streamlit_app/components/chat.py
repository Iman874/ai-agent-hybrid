# streamlit_app/components/chat.py
"""Chat tab — interactive TOR building via conversation."""

import streamlit as st
from utils.icons import mi, mi_inline
from utils.notify import notify
from state import back_to_active, reset_session
from api.client import send_message, handle_response, fetch_models
from components.tor_preview import render_tor_preview


def render_chat_tab():
    """Render tab Chat: empty state / messages / TOR preview / input."""

    # === HISTORY VIEW MODE ===
    if st.session_state.is_viewing_history:
        _render_history_view()
        return

    _render_chat_model_selector()
    st.divider()

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


def _render_chat_model_selector():
    """Compact model selector — hanya tampil di tab Chat."""
    models = fetch_models()
    local_models = [m for m in models if m["type"] == "local" and m["status"] == "available"]
    gemini_models = [m for m in models if m["type"] == "gemini" and m["status"] == "available"]

    mode_opts, mode_map = [], {}
    if local_models:
        mode_opts.append("Local LLM")
        mode_map["Local LLM"] = "local"
    if gemini_models:
        mode_opts.append("Gemini API")
        mode_map["Gemini API"] = "gemini"

    if not mode_opts:
        notify("Tidak ada model tersedia.", "error", method="inline")
        return

    current_label = next(
        (lbl for lbl, m in mode_map.items() if m == st.session_state.chat_mode),
        mode_opts[0],
    )

    col_radio, col_model = st.columns([1, 1])
    with col_radio:
        selected = st.radio(
            "Provider",
            mode_opts,
            index=mode_opts.index(current_label),
            horizontal=True,
            label_visibility="collapsed",
            key="chat_provider_radio",
        )

    new_mode = mode_map.get(selected, "local")
    chat_models: list[str] = []

    with col_model:
        if new_mode == "local" and local_models:
            chat_models = [
                m["id"] for m in local_models
                if "embed" not in m["id"].lower() and "nomic" not in m["id"].lower()
            ]
            if chat_models:
                st.selectbox(
                    "Model",
                    chat_models,
                    label_visibility="collapsed",
                    key="chat_model_select",
                )
        elif new_mode == "gemini" and gemini_models:
            st.caption(f"_{gemini_models[0]['id']}_")

    if new_mode != st.session_state.chat_mode:
        if st.session_state.session_id and st.session_state.messages:
            notify("Ganti model akan mereset session.", "warning", method="inline")
            if st.button("Konfirmasi Reset", use_container_width=True, key="model_reset_confirm"):
                st.session_state.chat_mode = new_mode
                reset_session()
                st.rerun()
        else:
            st.session_state.chat_mode = new_mode

    if new_mode == "local" and chat_models:
        active_model = chat_models[0]
        if active_model.endswith("-cloud"):
            think_on = st.toggle(
                "Deep Reasoning",
                value=st.session_state.thinking_mode,
                help="Matikan untuk response lebih cepat.",
                key="thinking_toggle",
            )
            if think_on != st.session_state.thinking_mode:
                st.session_state.thinking_mode = think_on

    offline = [m for m in models if m["type"] == "local" and m["status"] == "offline"]
    if offline and not local_models:
        st.markdown(
            mi_inline("cloud_off", "Ollama offline", 16, color="var(--color-text-muted)"),
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


def _render_history_view():
    """Tampilkan session lama dalam mode read-only."""
    hist = st.session_state.history_session

    if not hist:
        notify("Data session tidak tersedia.", "warning", method="inline")
        if st.button("← Kembali"):
            back_to_active()
            st.rerun()
        return

    # --- Banner Info ---
    session_title = hist.get("extracted_data", {}).get("judul") or f"Session {hist['id'][:8]}..."
    session_state = hist.get("state", "—")
    session_turns = hist.get("turn_count", 0)

    notify(
        f"Arsip session: {session_title}. Status: {session_state} · {session_turns} Turn. "
        "Mode read-only, tidak bisa mengirim pesan baru.",
        "info",
        icon="history",
        method="inline",
    )

    # --- Tombol Kembali ---
    if st.button("← Kembali ke Obrolan Aktif", type="primary"):
        back_to_active()
        st.rerun()

    st.divider()

    # --- Render Chat History (read-only) ---
    chat_history = hist.get("chat_history", [])

    if not chat_history:
        st.caption("_Session ini tidak memiliki riwayat chat._")
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
        st.caption("💡 Jika tombol export di atas error, gunakan fallback di bawah:")
        fb1, fb2 = st.columns(2)
        with fb1:
            st.download_button(
                "📝 Download .md (fallback)",
                data=generated_tor,
                file_name=f"tor_history_{hist['id'][:8]}.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_history_md_fb",
            )
