# streamlit_app/components/tor_preview.py
"""Reusable TOR document preview component."""

import streamlit as st
from utils.icons import mi, mi_inline, banner_html
from utils.formatters import export_to_pdf


def render_tor_preview(
    tor: dict,
    escalation_info: dict | None = None,
    key_suffix: str = "",
):
    """Render TOR preview lengkap: banner, metadata, content, downloads.

    Args:
        tor: TOR document dict {"content": "...", "metadata": {...}}
        escalation_info: Optional escalation data
        key_suffix: Unique key suffix untuk download buttons
    """
    st.divider()

    # --- Success banner ---
    st.markdown(
        banner_html("task_alt", "TOR Berhasil Dibuat!", "success"),
        unsafe_allow_html=True,
    )

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

    # --- Download Buttons ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇ Download .md",
            tor["content"],
            f"tor{key_suffix}.md",
            "text/markdown",
            use_container_width=True,
            key=f"dl_md{key_suffix}",
        )
    with c2:
        pdf = export_to_pdf(tor["content"])
        st.download_button(
            "⬇ Download .pdf",
            pdf,
            f"tor{key_suffix}.pdf",
            "application/pdf",
            use_container_width=True,
            key=f"dl_pdf{key_suffix}",
            disabled=not pdf,
        )

    # --- Escalation Warning ---
    if escalation_info:
        reason = escalation_info.get("reason", "")
        trigger = escalation_info.get("triggered_by", "")
        st.markdown(
            banner_html(
                "warning",
                f"TOR via eskalasi · <strong>{trigger}</strong> · {reason}",
                "warning",
            ),
            unsafe_allow_html=True,
        )
