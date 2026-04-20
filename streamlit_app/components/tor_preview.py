# streamlit_app/components/tor_preview.py
"""Reusable TOR document preview component."""

import streamlit as st
from utils.icons import mi, mi_inline
from utils.notify import notify
from api.client import export_document


def render_tor_preview(
    tor: dict,
    session_id: str,
    escalation_info: dict | None = None,
    key_suffix: str = "",
):
    """Render TOR preview lengkap: banner, metadata, content, downloads.

    Args:
        tor: TOR document dict {"content": "...", "metadata": {...}}
        session_id: ID session untuk fetch export dari backend API
        escalation_info: Optional escalation data
        key_suffix: Unique key suffix untuk download buttons
    """
    st.divider()

    # --- Success banner ---
    notify("TOR Berhasil Dibuat!", "success", method="banner")

    # --- Metadata (collapsible) ---
    with st.expander(
        mi_inline("info", "Metadata", 18) if False else "Metadata",
        expanded=False,
    ):
        meta = tor.get("metadata", {})
        c = st.columns(4)
        c[0].metric("Model", meta.get("generated_by", "—"))
        c[1].metric("Mode", meta.get("mode", "—"))
        c[2].metric("Kata", meta.get("word_count", 0))
        c[3].metric("Waktu", f'{meta.get("generation_time_ms", 0)}ms')

    # --- TOR Content ---
    st.markdown(tor["content"])

    # --- Download Buttons (via Backend API) ---
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        docx_bytes = export_document(session_id, "docx")
        st.download_button(
            "📄 Download .docx",
            data=docx_bytes or b"",
            file_name=f"tor{key_suffix}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key=f"dl_docx{key_suffix}",
            disabled=not docx_bytes,
        )

    with c2:
        pdf_bytes = export_document(session_id, "pdf")
        st.download_button(
            "📕 Download .pdf",
            data=pdf_bytes or b"",
            file_name=f"tor{key_suffix}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_pdf{key_suffix}",
            disabled=not pdf_bytes,
        )

    with c3:
        md_bytes = export_document(session_id, "md")
        st.download_button(
            "📝 Download .md",
            data=md_bytes or b"",
            file_name=f"tor{key_suffix}.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"dl_md{key_suffix}",
            disabled=not md_bytes,
        )

    # --- Escalation Warning ---
    if escalation_info:
        reason = escalation_info.get("reason", "")
        trigger = escalation_info.get("triggered_by", "")
        notify(
            f"TOR via eskalasi · {trigger} · {reason}",
            "warning",
            icon="warning",
            method="banner",
        )
