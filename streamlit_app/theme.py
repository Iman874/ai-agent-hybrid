# streamlit_app/theme.py
"""Theme engine — apply, switch, and persist theme preferences."""

import streamlit as st
from config import THEMES, THEME_FILE


def apply_saved_theme():
    """Apply theme dari saved preference saat startup.
    
    Harus dipanggil setelah init_session_state() di app.py.
    """
    mode = st.session_state.get("app_theme", "system")
    _apply_config(mode)


def switch_theme(new_mode: str):
    """Switch ke theme baru, simpan, dan rerun.
    
    Args:
        new_mode: "system" | "dark" | "light"
    """
    if new_mode == st.session_state.get("app_theme"):
        return  # same theme, no-op
    
    st.session_state.app_theme = new_mode
    _save_pref(new_mode)
    _apply_config(new_mode)
    st.rerun()


def get_current_theme() -> str:
    """Return current active theme name.
    
    Returns:
        str: "system" | "dark" | "light"
    """
    return st.session_state.get("app_theme", "system")


def _apply_config(mode: str):
    """Apply theme via st._config.set_option untuk BaseWeb components.
    
    - dark/light: Set semua theme options
    - system: Clear overrides agar Streamlit ikuti browser
    """
    if mode in THEMES:
        for key, value in THEMES[mode].items():
            try:
                st._config.set_option(f"theme.{key}", value)
            except Exception:
                pass
    else:
        # system mode: clear semua overrides
        for key in ["base", "primaryColor", "backgroundColor",
                    "secondaryBackgroundColor", "textColor"]:
            try:
                st._config.set_option(f"theme.{key}", "")
            except Exception:
                pass


def _save_pref(mode: str):
    """Persist theme preference ke file."""
    try:
        THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
        THEME_FILE.write_text(mode)
    except Exception:
        pass  # non-critical
