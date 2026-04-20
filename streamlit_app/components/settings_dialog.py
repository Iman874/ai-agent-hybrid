"""Settings dialog - ChatGPT-style sidebar navigation."""

from __future__ import annotations

import streamlit as st
from config import API_URL
from state import begin_ui_action, end_ui_action, next_ui_action_id
from theme import get_current_theme, switch_theme
from utils.notify import notify
from utils.i18n import get_language, set_language, tr
from components.format_tab import render_format_settings


def _run_dialog_rerun(changed: bool) -> None:
    """Rerun dialog dengan scoped mode jika tersedia, fallback global jika tidak."""
    if not changed:
        return
    try:
        st.rerun(scope="fragment")
    except TypeError:
        st.rerun()
    except Exception:
        st.rerun()


def _run_app_rerun(changed: bool) -> None:
    """Rerun full app untuk perubahan global yang harus sinkron lintas komponen."""
    if not changed:
        return
    st.rerun()


def _switch_settings_section(next_section: str) -> None:
    """Pindah section settings dengan event guard anti double-trigger."""
    current_section = st.session_state.get("_settings_section", "umum")
    if next_section == current_section:
        return

    action_id = next_ui_action_id(f"settings:section:{next_section}")
    if not begin_ui_action(action_id):
        return

    try:
        st.session_state._settings_section = next_section
    finally:
        end_ui_action(action_id)

    _run_dialog_rerun(changed=True)


@st.dialog("Settings / Pengaturan", width="large")
def show_settings_dialog() -> None:
    """Dialog pengaturan dengan navigasi kiri dan konten kanan."""
    col_nav, col_content = st.columns([1, 3])

    with col_nav:
        nav_items = {
            "umum": tr("settings.nav.general", "Umum"),
            "format_tor": tr("settings.nav.format_tor", "Format TOR"),
            "lanjutan": tr("settings.nav.advanced", "Lanjutan"),
        }
        current = st.session_state.get("_settings_section", "umum")

        for key, label in nav_items.items():
            btn_type = "primary" if key == current else "secondary"
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                _switch_settings_section(key)

    with col_content:
        section = st.session_state.get("_settings_section", "umum")

        if section == "umum":
            _render_general_settings()
        elif section == "format_tor":
            _render_format_tor_settings()
        elif section == "lanjutan":
            _render_advanced_settings()


def _render_general_settings() -> None:
    """Section Umum - tema dan bahasa."""
    st.markdown(f"#### {tr('settings.section.appearance', 'Penampilan')}")
    current = get_current_theme()
    options = {
        "system": tr("settings.theme.system", "Default sistem"),
        "dark": tr("settings.theme.dark", "Gelap"),
        "light": tr("settings.theme.light", "Terang"),
    }
    keys = list(options.keys())
    selected = st.radio(
        tr("settings.theme.label", "Tema"),
        keys,
        format_func=lambda k: options[k],
        index=keys.index(current) if current in keys else 0,
        label_visibility="collapsed",
    )

    if selected != current:
        switch_theme(selected)

    st.divider()
    st.markdown(f"#### {tr('settings.section.language', 'Bahasa')}")

    lang_options = {
        "id": tr("settings.language.id", "Bahasa Indonesia"),
        "en": tr("settings.language.en", "English"),
    }
    lang_keys = list(lang_options.keys())
    current_lang = get_language()
    selected_lang = st.radio(
        tr("settings.language.label", "Bahasa"),
        lang_keys,
        format_func=lambda k: lang_options[k],
        index=lang_keys.index(current_lang) if current_lang in lang_keys else 0,
        label_visibility="collapsed",
    )

    if selected_lang != current_lang:
        action_id = next_ui_action_id(f"settings:language:{selected_lang}")
        if begin_ui_action(action_id):
            try:
                set_language(selected_lang)
            finally:
                end_ui_action(action_id)
            # Bahasa mempengaruhi seluruh app, jadi wajib rerun full app.
            _run_app_rerun(changed=True)


def _render_format_tor_settings() -> None:
    """Section Format TOR - style management."""
    st.markdown(f"#### {tr('settings.section.format_tor', 'Format TOR')}")
    render_format_settings(show_header=False)


def _render_advanced_settings() -> None:
    """Section Lanjutan - pengaturan teknis."""
    st.markdown(f"#### {tr('settings.section.advanced', 'Pengaturan Lanjutan')}")
    st.caption(tr("settings.advanced.caption", "Pengaturan teknis untuk developer."))

    with st.expander(tr("settings.advanced.api_endpoint", "API Endpoint")):
        st.code(API_URL)

    with st.expander(tr("settings.advanced.cache", "Cache")):
        if st.button(tr("settings.advanced.clear_cache", "Hapus Cache"), key="clear_cache"):
            st.cache_data.clear()
            notify(tr("settings.cache_cleared", "Cache berhasil dihapus."), "success")
