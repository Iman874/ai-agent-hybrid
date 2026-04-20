# streamlit_app/components/form_document.py
"""From Document tab — generate TOR from uploaded document."""

from time import perf_counter

import streamlit as st
from utils.icons import mi
from utils.i18n import tr
from utils.notify import notify
from api.client import generate_from_document, get_active_style
from components.tor_preview import render_tor_preview
from state import begin_ui_action, end_ui_action, next_ui_action_id, record_perf_sample


def render_document_tab():
    """Render tab From Document: file upload + generate."""

    if st.session_state.is_viewing_history:
        notify(
            tr("doc.history_view_info", "Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini."),
            "info",
            icon="history",
            method="inline",
        )
        return

    st.markdown(
        f"### {mi('upload_file', 24, 'var(--color-primary)')} {tr('doc.title', 'Generate TOR dari Dokumen')}",
        unsafe_allow_html=True,
    )
    st.caption(tr("doc.subtitle", "Upload dokumen sumber, Gemini otomatis membuat TOR."))

    active = get_active_style()
    active_name = active.get("name", tr("common.default", "Default")) if active else tr("common.default", "Default")
    st.caption(
        tr(
            "doc.active_format_caption",
            "Format yang digunakan: **{active_name}** - ubah di Pengaturan > Format TOR",
            active_name=active_name,
        )
    )

    uploaded_file = st.file_uploader(
        tr("doc.upload_label", "Upload dokumen"),
        type=["pdf", "txt", "md", "docx"],
        help=tr("doc.upload_help", "Format: PDF, TXT, MD, DOCX. Maks 20MB."),
    )
    doc_context = st.text_area(
        tr("doc.context_label", "Konteks tambahan (opsional)"),
        placeholder=tr("doc.context_placeholder", "Contoh: Ini lanjutan workshop tahun lalu..."),
        height=100,
    )

    if st.button(
        tr("doc.generate_button", "Generate TOR"),
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        if uploaded_file:
            action_id = next_ui_action_id("doc:generate")
            if begin_ui_action(action_id):
                t0 = perf_counter()
                try:
                    changed = _handle_generate(uploaded_file, doc_context)
                finally:
                    end_ui_action(action_id)
                    record_perf_sample("doc_generate", (perf_counter() - t0) * 1000)
                if changed:
                    st.rerun()

    # Show result
    if st.session_state.doc_tor:
        render_tor_preview(
            st.session_state.doc_tor,
            session_id=st.session_state.get("doc_session_id", ""),
            key_suffix="_doc",
        )
        if st.button(tr("doc.generate_again", "Generate Ulang"), key="reset_doc"):
            action_id = next_ui_action_id("doc:reset")
            if begin_ui_action(action_id):
                try:
                    had_value = st.session_state.doc_tor is not None
                    st.session_state.doc_tor = None
                    st.session_state.doc_session_id = None
                finally:
                    end_ui_action(action_id)
                if had_value:
                    st.rerun()


def _handle_generate(uploaded_file, context: str) -> bool:
    """Process uploaded file dan generate TOR (pakai active style)."""
    with st.spinner(tr("doc.spinner", "Membaca dokumen dan generating TOR...")):
        result = generate_from_document(
            uploaded_file.read(),
            uploaded_file.name,
            context,
        )

    if "error" in result:
        notify(result["error"], "error", method="banner")
        return False

    previous_tor = st.session_state.get("doc_tor")
    previous_session_id = st.session_state.get("doc_session_id")
    st.session_state.doc_tor = result.get("tor_document", result)
    st.session_state.doc_session_id = result.get("session_id", "")
    return (
        st.session_state.doc_tor != previous_tor
        or st.session_state.doc_session_id != previous_session_id
    )
