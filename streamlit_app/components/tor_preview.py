# streamlit_app/components/tor_preview.py
"""Reusable TOR document preview component."""

import streamlit as st
from utils.icons import mi_inline
from utils.notify import notify
from api.client import export_document


def _get_export_cache() -> dict[str, bytes]:
    """Ambil/siapkan cache export TOR per session-state."""
    cache = st.session_state.get("_tor_export_cache")
    if isinstance(cache, dict):
        return cache
    st.session_state._tor_export_cache = {}
    return st.session_state._tor_export_cache


def _export_cache_key(session_id: str, key_suffix: str, fmt: str) -> str:
    """Build key cache unik untuk kombinasi session, view, dan format."""
    return f"{session_id}:{key_suffix}:{fmt}"


def _prepare_export(session_id: str, key_suffix: str, fmt: str) -> bytes | None:
    """Fetch export dari API hanya saat diminta user dan simpan ke cache lokal."""
    cache = _get_export_cache()
    cache_key = _export_cache_key(session_id, key_suffix, fmt)
    cached = cache.get(cache_key)
    if cached:
        return cached

    content = export_document(session_id, fmt)
    if content:
        cache[cache_key] = content
        st.session_state._tor_export_cache = cache
    return content


def _render_lazy_download(
    session_id: str,
    key_suffix: str,
    fmt: str,
    icon: str,
    mime: str,
) -> None:
    """Render tombol prepare/download untuk satu format file export."""
    cache_key = _export_cache_key(session_id, key_suffix, fmt)
    cached_bytes = _get_export_cache().get(cache_key)

    if cached_bytes:
        st.download_button(
            f"{icon} Download .{fmt}",
            data=cached_bytes,
            file_name=f"tor{key_suffix}.{fmt}",
            mime=mime,
            use_container_width=True,
            key=f"dl_{fmt}{key_suffix}",
        )
        return

    if st.button(
        f"{icon} Siapkan .{fmt}",
        key=f"prep_{fmt}{key_suffix}",
        use_container_width=True,
    ):
        with st.spinner(f"Menyiapkan .{fmt}..."):
            prepared = _prepare_export(session_id, key_suffix, fmt)
        if prepared:
            st.rerun()


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

    # --- Download Buttons (lazy export; no render-time API call) ---
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        _render_lazy_download(
            session_id=session_id,
            key_suffix=key_suffix,
            fmt="docx",
            icon="📄",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    with c2:
        _render_lazy_download(
            session_id=session_id,
            key_suffix=key_suffix,
            fmt="pdf",
            icon="📕",
            mime="application/pdf",
        )

    with c3:
        _render_lazy_download(
            session_id=session_id,
            key_suffix=key_suffix,
            fmt="md",
            icon="📝",
            mime="text/markdown",
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
