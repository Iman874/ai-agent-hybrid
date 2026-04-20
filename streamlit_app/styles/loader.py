# streamlit_app/styles/loader.py
"""CSS and font injection for Streamlit."""

import streamlit as st
from pathlib import Path
from time import perf_counter

from state import record_perf_sample

STYLES_DIR = Path(__file__).parent


@st.cache_data
def _load_css_bundle(css_version: tuple[int, int]) -> str:
    """Load dan gabungkan CSS dari disk; cache invalidates when file version changes."""
    _ = css_version
    base_css = (STYLES_DIR / "base.css").read_text()
    components_css = (STYLES_DIR / "components.css").read_text()
    return f"{base_css}\n\n{components_css}"


def _css_version() -> tuple[int, int]:
    """Return file mtimes so cache refreshes when CSS files are edited."""
    base_path = STYLES_DIR / "base.css"
    components_path = STYLES_DIR / "components.css"
    return (base_path.stat().st_mtime_ns, components_path.stat().st_mtime_ns)


def _task12_mode_text_color() -> str:
    """Deterministic readable text color for Task12 based on selected app theme."""
    mode = st.session_state.get("app_theme", "system")
    if mode == "light":
        return "#1f2328"
    if mode == "dark":
        return "#e6edf3"
    return "var(--text-color, var(--color-text))"


def inject_styles():
    """Inject Google Fonts, Material Icons, dan custom CSS ke halaman."""
    t0 = perf_counter()
    merged_css = _load_css_bundle(_css_version())
    task12_text_color = _task12_mode_text_color()

    html_str = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

:root {{
  --task12-mode-text: {task12_text_color};
}}

{merged_css}
</style>
"""
    st.markdown(html_str.strip(), unsafe_allow_html=True)
    record_perf_sample("styles_inject", (perf_counter() - t0) * 1000)
