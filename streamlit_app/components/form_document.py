# streamlit_app/components/form_document.py
"""From Document tab — generate TOR from uploaded document."""

import streamlit as st
from utils.icons import mi, banner_html
from api.client import generate_from_document
from components.tor_preview import render_tor_preview


def render_document_tab():
    """Render tab From Document: file upload + generate."""

    st.markdown(
        f"### {mi('upload_file', 24, 'var(--color-primary)')} Generate TOR dari Dokumen",
        unsafe_allow_html=True,
    )
    st.caption("Upload dokumen sumber, Gemini otomatis membuat TOR.")

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
        render_tor_preview(st.session_state.doc_tor, key_suffix="_doc")
        if st.button("Generate Ulang", key="reset_doc"):
            st.session_state.doc_tor = None
            st.rerun()


def _handle_generate(uploaded_file, context: str):
    """Process uploaded file dan generate TOR."""
    with st.spinner("Membaca dokumen dan generating TOR..."):
        result = generate_from_document(
            uploaded_file.read(),
            uploaded_file.name,
            context,
        )

    if "error" in result:
        st.markdown(
            banner_html("error", result["error"], "error"),
            unsafe_allow_html=True,
        )
    else:
        st.session_state.doc_tor = result.get("tor_document", result)
        st.rerun()
