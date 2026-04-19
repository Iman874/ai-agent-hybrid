# streamlit_app/config.py
"""Application constants and configuration."""

from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).parent.parent          # project root
STREAMLIT_DIR = ROOT / ".streamlit"
THEME_FILE = STREAMLIT_DIR / ".current_theme"
CSS_DIR = Path(__file__).parent / "styles"

# --- API ---
API_URL = "http://localhost:8000/api/v1"

# --- Page Config ---
PAGE_CONFIG = {
    "page_title": "TOR Generator — AI Agent Hybrid",
    "page_icon": "📝",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# --- TOR Fields ---
REQUIRED_FIELDS = [
    "judul", "latar_belakang", "tujuan",
    "ruang_lingkup", "output", "timeline",
]
OPTIONAL_FIELDS = ["estimasi_biaya"]

FIELD_LABELS = {
    "judul": "Judul Kegiatan",
    "latar_belakang": "Latar Belakang",
    "tujuan": "Tujuan",
    "ruang_lingkup": "Ruang Lingkup",
    "output": "Output / Deliverable",
    "timeline": "Timeline",
    "estimasi_biaya": "Estimasi Biaya",
}

# --- Theme Definitions ---
THEMES = {
    "dark": {
        "base": "dark",
        "primaryColor": "#58a6ff",
        "backgroundColor": "#0d1117",
        "secondaryBackgroundColor": "#161b22",
        "textColor": "#e6edf3",
    },
    "light": {
        "base": "light",
        "primaryColor": "#0066cc",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f5f5f5",
        "textColor": "#111111",
    },
}
