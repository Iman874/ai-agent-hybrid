# streamlit_app/components/form_document.py
"""From Document tab — generate TOR from uploaded document."""

import streamlit as st
from utils.icons import mi
from utils.notify import notify
from api.client import generate_from_document, get_active_style
from components.tor_preview import render_tor_preview


def render_document_tab():
    """Render tab From Document: file upload + generate."""

    if st.session_state.is_viewing_history:
        notify(
            "Anda sedang melihat arsip session. Kembali ke obrolan aktif untuk menggunakan fitur ini.",
            "info",
            icon="history",
            method="inline",
        )
        return

    st.markdown(
        f"### {mi('upload_file', 24, 'var(--color-primary)')} Generate TOR dari Dokumen",
        unsafe_allow_html=True,
    )
    st.caption("Upload dokumen sumber, Gemini otomatis membuat TOR.")

    active = get_active_style()
    active_name = active.get("name", "Default") if active else "Default"
    st.caption(f"🎨 Format yang digunakan: **{active_name}** — ubah di tab Format TOR")

    uploaded_file = st.file_uploader(
        "Upload dokumen",
        type=["pdf", "txt", "md", "docx"],
        help="Format: PDF, TXT, MD, DOCX. Maks 20MB.",
    )
    doc_context = st.text_area(
        "Konteks tambahan (opsional)",
        placeholder="Contoh: Ini lanjutan workshop tahun lalu...",
        height=100,
    )

    if st.button(
        "Generate TOR",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        if uploaded_file:
            _handle_generate(uploaded_file, doc_context)

    # Show result
    if st.session_state.doc_tor:
        render_tor_preview(
            st.session_state.doc_tor,
            session_id=st.session_state.get("doc_session_id", ""),
            key_suffix="_doc",
        )
        if st.button("Generate Ulang", key="reset_doc"):
            st.session_state.doc_tor = None
            st.rerun()


def _handle_generate(uploaded_file, context: str):
    """Process uploaded file dan generate TOR (pakai active style)."""
    with st.spinner("Membaca dokumen dan generating TOR..."):
        result = generate_from_document(
            uploaded_file.read(),
            uploaded_file.name,
            context,
        )

    if "error" in result:
        notify(result["error"], "error", method="banner")
    else:
        st.session_state.doc_tor = result.get("tor_document", result)
        st.session_state.doc_session_id = result.get("session_id", "")
        st.rerun()
