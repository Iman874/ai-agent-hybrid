# Task 01: Scaffold Architecture — Folder Structure + Config + State

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat struktur folder modular dan file fondasi (`config.py`, `state.py`).

## 2. Deskripsi

Memecah file monolitik `streamlit_app.py` (564 baris) dimulai dengan membuat
skeleton folder `streamlit_app/` beserta dua file fondasi yang akan digunakan
oleh semua modul lain: `config.py` (constants) dan `state.py` (session state
manager).

## 3. Tujuan Teknis

- Buat folder `streamlit_app/` dengan sub-folder `api/`, `components/`, `utils/`, `styles/`
- Buat `__init__.py` di setiap package
- Extract semua constants ke `config.py`
- Extract semua session state logic ke `state.py`
- Pastikan import path benar saat dijalankan via `streamlit run streamlit_app/app.py`

## 4. Scope

**Yang dikerjakan:**
- Membuat folder structure lengkap
- `config.py` — semua constants (API_URL, THEME_FILE, PAGE_CONFIG, FIELDS, THEMES)
- `state.py` — `init_session_state()`, `reset_session()`, `_load_theme_pref()`
- `app.py` placeholder (kosong, hanya import test)

**Yang TIDAK dikerjakan:**
- Belum membuat komponen UI apapun
- Belum membuat CSS / icons / API client
- File monolit `streamlit_app.py` belum dihapus

## 5. Langkah Implementasi

### Step 1: Buat folder structure

```
mkdir streamlit_app
mkdir streamlit_app/api
mkdir streamlit_app/components
mkdir streamlit_app/utils
mkdir streamlit_app/styles
```

### Step 2: Buat semua `__init__.py`

```
touch streamlit_app/__init__.py
touch streamlit_app/api/__init__.py
touch streamlit_app/components/__init__.py
touch streamlit_app/utils/__init__.py
touch streamlit_app/styles/__init__.py
```

### Step 3: Buat `config.py`

Extract dari `streamlit_app.py` lines 16-36:

```python
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
```

### Step 4: Buat `state.py`

Extract dari `streamlit_app.py` lines 224-296:

```python
# streamlit_app/state.py
"""Session state initialization and management."""

import streamlit as st
from config import THEME_FILE


def init_session_state():
    """Initialize semua session state keys dengan default values.
    
    Dipanggil sekali di app.py sebelum render apapun.
    """
    defaults = {
        "session_id": None,
        "messages": [],
        "current_state": {
            "status": "NEW",
            "turn_count": 0,
            "completeness_score": 0.0,
            "filled_fields": [],
            "missing_fields": [],
        },
        "tor_document": None,
        "escalation_info": None,
        "direct_tor": None,
        "doc_tor": None,
        "chat_mode": "local",
        "app_theme": _load_theme_pref(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session():
    """Reset chat session tanpa menghapus theme/mode preferences."""
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW",
        "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [],
        "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None


def _load_theme_pref() -> str:
    """Baca pilihan theme dari file. Default: 'system'."""
    if THEME_FILE.exists():
        val = THEME_FILE.read_text().strip()
        if val in ("system", "dark", "light"):
            return val
    return "system"
```

### Step 5: Buat placeholder `app.py`

```python
# streamlit_app/app.py
"""Entry point — TOR Generator UI."""

import streamlit as st
from config import PAGE_CONFIG
from state import init_session_state

# --- Bootstrap ---
st.set_page_config(**PAGE_CONFIG)
init_session_state()

st.title("🔨 Beta 0.1.8 — Scaffold OK")
st.write(f"Theme preference: {st.session_state.app_theme}")
st.write(f"Chat mode: {st.session_state.chat_mode}")
```

### Step 6: Test

```powershell
streamlit run streamlit_app/app.py --server.port 8501
```

Pastikan halaman tampil tanpa error.

## 6. Output yang Diharapkan

```
streamlit_app/
├── __init__.py          (kosong)
├── app.py               (~10 lines, placeholder)
├── config.py            (~60 lines)
├── state.py             (~55 lines)
├── api/
│   └── __init__.py
├── components/
│   └── __init__.py
├── utils/
│   └── __init__.py
└── styles/
    └── __init__.py
```

Browser menampilkan: "Beta 0.1.8 — Scaffold OK" + theme/mode info.

## 7. Dependencies

Tidak ada — ini task pertama.

## 8. Acceptance Criteria

- [ ] Folder `streamlit_app/` ada dengan semua sub-folder
- [ ] Semua `__init__.py` ada
- [ ] `config.py` berisi semua constants (API_URL, PAGE_CONFIG, FIELDS, THEMES)
- [ ] `state.py` berisi `init_session_state()` dan `reset_session()`
- [ ] `streamlit run streamlit_app/app.py` berjalan tanpa error
- [ ] Session state ter-inisialisasi dengan benar
- [ ] File monolit `streamlit_app.py` BELUM dihapus (masih jadi referensi)

## 9. Estimasi

**Low** — Hanya membuat struktur dan memindahkan data/logic yang sudah ada.
