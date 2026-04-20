# streamlit_app/components/header.py
"""Header area — title bar + theme toggle popover."""

import streamlit as st
from utils.icons import mi
from theme import switch_theme, get_current_theme


def render_header():
    """Render header: title (left) + theme menu (right)."""
    col_title, col_menu = st.columns([9, 1])

    with col_title:
        icon = mi("smart_toy", 22, "var(--color-primary)")

        st.markdown(
            f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
            f'{icon} TOR Generator'
            f'</h3>',
            unsafe_allow_html=True,
        )

    with col_menu:
        _render_theme_popover()


def _render_theme_popover():
    """Popover menu untuk toggle tema (System / Dark / Light)."""
    current = get_current_theme()

    THEME_OPTIONS = [
        ("desktop_windows", "Ikuti Sistem", "system"),
        ("dark_mode", "Gelap", "dark"),
        ("light_mode", "Terang", "light"),
    ]

    # Cari index opsi saat ini
    current_index = next(
        (i for i, (_, _, val) in enumerate(THEME_OPTIONS) if val == current),
        0,
    )

    with st.popover("⋮"):
        st.caption("Tampilan")
        labels = [text for _, text, _ in THEME_OPTIONS]
        selected = st.radio(
            "theme",
            labels,
            index=current_index,
            label_visibility="collapsed",
        )

        # Map label → value
        selected_value = next(
            val for _, text, val in THEME_OPTIONS if text == selected
        )

        if selected_value != current:
            switch_theme(selected_value)
