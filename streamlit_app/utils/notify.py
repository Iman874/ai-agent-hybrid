"""Unified notification system for Streamlit UI.

Semua notifikasi ke user harus melalui fungsi `notify()`.
Jangan gunakan st.error/st.warning/st.success/st.info secara langsung lagi.
"""

import streamlit as st
from .icons import mi, banner_html

_DEFAULT_ICONS = {
    "success": "task_alt",
    "error": "error",
    "warning": "warning",
    "info": "info",
}

_TOAST_EMOJI = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}

_ST_ICON_MAP = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}


def notify(
    message: str,
    type: str = "info",
    icon: str | None = None,
    method: str = "toast",
) -> None:
    """Tampilkan notifikasi ke user.

    Args:
        message: Pesan untuk ditampilkan
        type: Jenis notifikasi — "success" | "error" | "warning" | "info"
        icon: Nama Material Symbol (auto-detect jika None)
        method: Cara tampil — "toast" | "banner" | "inline"

    Methods:
        - toast: muncul di pojok kanan atas, hilang otomatis (untuk konfirmasi ringan)
        - banner: HTML banner di body halaman, persistent (untuk hasil penting)
        - inline: st.info/error/warning/success bawaan (untuk guard clause / in-place)
    """
    resolved_icon = icon or _DEFAULT_ICONS.get(type, "info")

    if method == "toast":
        _render_toast(message, type)
    elif method == "banner":
        _render_banner(message, type, resolved_icon)
    elif method == "inline":
        _render_inline(message, type)
    else:
        _render_toast(message, type)


def _render_toast(message: str, type: str) -> None:
    """Render notifikasi sebagai toast (pojok kanan atas, auto-dismiss)."""
    emoji = _TOAST_EMOJI.get(type, "ℹ️")
    st.toast(f"{emoji} {message}")


def _render_banner(message: str, type: str, icon_name: str) -> None:
    """Render notifikasi sebagai banner HTML (persistent di body)."""
    st.markdown(
        banner_html(icon_name, message, type),
        unsafe_allow_html=True,
    )


def _render_inline(message: str, type: str) -> None:
    """Render notifikasi inline menggunakan st.info/error/warning/success."""
    func_map = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info,
    }
    func = func_map.get(type, st.info)
    st_icon = _ST_ICON_MAP.get(type)
    if st_icon:
        func(message, icon=st_icon)
    else:
        func(message)
