# streamlit_app/styles/loader.py
"""CSS and font injection for Streamlit."""

import streamlit as st
from pathlib import Path

STYLES_DIR = Path(__file__).parent


def inject_styles():
    """Inject Google Fonts, Material Icons, dan custom CSS ke halaman."""
    base_css = (STYLES_DIR / "base.css").read_text()
    components_css = (STYLES_DIR / "components.css").read_text()

    html_str = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

{base_css}

{components_css}
</style>
"""
    st.markdown(html_str.strip(), unsafe_allow_html=True)
