# 🎨 Plan Design — Beta 0.1.8: Total UI Redesign & Modular Architecture

> **Modul**: Production-Ready UI Redesign + Modular Streamlit Architecture
> **Versi**: beta0.1.8
> **Status**: Plan Ready — Menunggu Review
> **Prasyarat**: beta0.1.7 selesai (Chat UI Overhaul + Model Selector)

---

## 1. Ringkasan Modul

Beta 0.1.8 adalah **redesign total** UI Streamlit dari prototype menjadi aplikasi production-ready.

### Masalah Utama di v0.1.7

| # | Masalah | Dampak |
|---|---------|--------|
| 1 | File monolitik 564 baris (`streamlit_app.py`) | Sulit maintain, tidak scalable |
| 2 | Penggunaan emoji sebagai icon (🤖, 🚀, 📄...) | Tidak konsisten, tidak profesional, rendering beda antar OS |
| 3 | Design system tidak ada | Warna, spacing, typography ad-hoc |
| 4 | Theme switching via `st._config` hack | Fragile, menggunakan private API |
| 5 | Empty state / error state generik | UX tidak terarah |
| 6 | Layout ChatGPT clone tapi belum polish | Terlihat seperti demo, bukan production |

### Target Beta 0.1.8

| # | Target | Detail |
|---|--------|--------|
| 1 | **Modular architecture** | Pecah monolit menjadi 12+ file terstruktur |
| 2 | **Material Icons** | Ganti semua emoji dengan Google Material Icons |
| 3 | **Design system** | Token warna, typography, spacing yang konsisten |
| 4 | **Production UX** | Loading, empty, error, success states yang jelas |
| 5 | **Theme engine stabil** | Tanpa private API hack, CSS-driven dengan fallback |

---

## 2. Arsitektur Baru

### 2.1 Current vs New Structure

```
SEBELUM (v0.1.7):                        SESUDAH (v0.1.8):
──────────────────                        ──────────────────
streamlit_app.py (564 lines, SEMUA)       streamlit_app/
                                          ├── app.py              ← entry point (40 lines)
                                          ├── config.py           ← constants & settings
                                          ├── state.py            ← session state manager
                                          ├── theme.py            ← theme engine
                                          │
                                          ├── api/
                                          │   ├── __init__.py
                                          │   └── client.py       ← semua API calls
                                          │
                                          ├── components/
                                          │   ├── __init__.py
                                          │   ├── sidebar.py      ← sidebar lengkap
                                          │   ├── header.py       ← header + theme toggle
                                          │   ├── chat.py         ← tab chat UI
                                          │   ├── form_direct.py  ← tab Gemini Direct
                                          │   ├── form_document.py← tab From Document
                                          │   └── tor_preview.py  ← TOR result viewer
                                          │
                                          ├── utils/
                                          │   ├── __init__.py
                                          │   ├── formatters.py   ← PDF export, text format
                                          │   └── icons.py        ← Material Icons helper
                                          │
                                          └── styles/
                                              ├── __init__.py
                                              ├── base.css         ← design system tokens
                                              ├── components.css   ← component-specific styles
                                              └── loader.py        ← CSS injection helper
```

### 2.2 Entry Point (`app.py`) — Target: ≤50 Lines

```python
# streamlit_app/app.py — clean entry point

import streamlit as st
from config import PAGE_CONFIG
from state import init_session_state
from theme import apply_saved_theme
from styles.loader import inject_styles
from components.sidebar import render_sidebar
from components.header import render_header
from components.chat import render_chat_tab
from components.form_direct import render_direct_tab
from components.form_document import render_document_tab

# --- Bootstrap ---
st.set_page_config(**PAGE_CONFIG)
init_session_state()
apply_saved_theme()
inject_styles()

# --- Layout ---
render_sidebar()
render_header()

tab_chat, tab_direct, tab_doc = st.tabs([
    "Chat", "Gemini Direct", "Dari Dokumen"
])

with tab_chat:
    render_chat_tab()
with tab_direct:
    render_direct_tab()
with tab_doc:
    render_document_tab()
```

> **Prinsip**: `app.py` hanya meng-compose — tidak mengandung logic apapun.

### 2.3 Dependency Flow

```
app.py
  ├── config.py          (pure data, tidak import apapun)
  ├── state.py           (depends on: config)
  ├── theme.py           (depends on: config, state)
  ├── styles/loader.py   (depends on: theme, config)
  │
  ├── components/
  │   ├── sidebar.py     (depends on: state, api/client, config, utils/icons)
  │   ├── header.py      (depends on: state, theme, utils/icons)
  │   ├── chat.py        (depends on: state, api/client, components/tor_preview, utils/icons)
  │   ├── form_direct.py (depends on: state, api/client, components/tor_preview, utils/icons)
  │   ├── form_document.py (depends on: state, api/client, components/tor_preview, utils/icons)
  │   └── tor_preview.py (depends on: utils/formatters, utils/icons)
  │
  ├── api/client.py      (depends on: config)
  │
  └── utils/
      ├── formatters.py  (pure functions)
      └── icons.py       (pure functions)
```

---

## 3. Design System

### 3.1 Warna — Token System

Semua warna didefinisikan sebagai CSS custom properties di `base.css`, sehingga theme switching hanya perlu mengganti root variables.

```css
/* === DARK THEME (default) === */
:root {
  /* Brand */
  --color-primary:     #58a6ff;
  --color-primary-hover: #79b8ff;
  --color-accent:      #a78bfa;     /* violet untuk highlight */

  /* Surface */
  --color-bg:          #0d1117;
  --color-bg-elevated: #161b22;
  --color-bg-card:     #1c2028;
  --color-bg-input:    #21262d;

  /* Text */
  --color-text:        #e6edf3;
  --color-text-muted:  #8b949e;
  --color-text-subtle: #6e7681;

  /* Border */
  --color-border:      #30363d;
  --color-border-hover:#484f58;

  /* Semantic */
  --color-success:     #3fb950;
  --color-warning:     #d29922;
  --color-error:       #f85149;
  --color-info:        #58a6ff;

  /* Spacing scale (8px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;

  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,.4);
  --shadow-lg: 0 8px 24px rgba(0,0,0,.5);

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --text-xs:  0.75rem;    /* 12px */
  --text-sm:  0.8125rem;  /* 13px */
  --text-base: 0.875rem;  /* 14px */
  --text-lg:  1rem;       /* 16px */
  --text-xl:  1.25rem;    /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 1.875rem;   /* 30px */

  /* Transition */
  --transition-fast: 150ms ease;
  --transition-base: 250ms ease;
}
```

### 3.2 Warna — Light Theme Override

```css
/* === LIGHT THEME === */
:root[data-theme="light"],
.light-theme {
  --color-primary:     #0066cc;
  --color-primary-hover: #0052a3;
  --color-accent:      #7c3aed;

  --color-bg:          #ffffff;
  --color-bg-elevated: #f6f8fa;
  --color-bg-card:     #ffffff;
  --color-bg-input:    #f0f2f5;

  --color-text:        #1f2328;
  --color-text-muted:  #656d76;
  --color-text-subtle: #8b949e;

  --color-border:      #d0d7de;
  --color-border-hover:#afb8c1;

  --color-success:     #1a7f37;
  --color-warning:     #9a6700;
  --color-error:       #cf222e;
  --color-info:        #0969da;

  --shadow-sm: 0 1px 2px rgba(0,0,0,.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,.1);
  --shadow-lg: 0 8px 24px rgba(0,0,0,.12);
}
```

### 3.3 Typography — Google Fonts

```html
<!-- Dimuat via CSS injection -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

| Element | Font | Weight | Size |
|---------|------|--------|------|
| Body text | Inter | 400 | `--text-base` (14px) |
| Labels / captions | Inter | 500 | `--text-sm` (13px) |
| Section headers | Inter | 600 | `--text-lg` (16px) |
| Page title | Inter | 700 | `--text-2xl` (24px) |
| Code / session ID | JetBrains Mono | 400 | `--text-sm` (13px) |

---

## 4. Material Icons — Mapping & Integration

### 4.1 Cara Integrasi

**Langkah 1**: Load Material Symbols font via CSS injection di `styles/loader.py`:

```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL@20..48,100..700,0..1" rel="stylesheet">
```

**Langkah 2**: Helper function di `utils/icons.py`:

```python
# utils/icons.py

def mi(name: str, size: int = 20, color: str = None, filled: bool = False) -> str:
    """Render Material Icon sebagai inline HTML.
    
    Args:
        name: Nama icon dari Material Symbols (e.g. "chat", "auto_awesome")
        size: Ukuran dalam pixel
        color: CSS color value (optional)
        filled: Apakah icon solid/filled
    
    Returns:
        HTML string <span> element
    """
    style_parts = [f"font-size:{size}px", "vertical-align:middle"]
    if color:
        style_parts.append(f"color:{color}")
    fill = "font-variation-settings:'FILL' 1;" if filled else ""
    style = ";".join(style_parts)
    return f'<span class="material-symbols-outlined" style="{style}{fill}">{name}</span>'


def mi_inline(name: str, text: str, size: int = 20, gap: int = 6) -> str:
    """Material Icon + text dalam satu baris."""
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{gap}px;">'
        f'{mi(name, size)} {text}'
        f'</span>'
    )
```

**Langkah 3**: Penggunaan di components:

```python
# Contoh di sidebar.py
st.markdown(mi_inline("smart_toy", "TOR Generator", 28), unsafe_allow_html=True)
st.markdown(mi_inline("add_comment", "Obrolan baru", 18), unsafe_allow_html=True)
```

### 4.2 Icon Mapping — Seluruh Aplikasi

Berikut mapping lengkap dari emoji → Material Symbol yang digunakan di seluruh UI:

#### Sidebar

| Lokasi | Sebelum (emoji) | Sesudah (Material) | Icon Name |
|--------|------------------|---------------------|-----------|
| Brand/Logo | 🤖 | `smart_toy` | `smart_toy` |
| New Chat button | ✏️ | `add_comment` | `add_comment` |
| Section: Model | ⚙️ | `tune` | `tune` |
| Local LLM option | 🖥️ | `computer` | `computer` |
| Gemini API option | ✨ | `auto_awesome` | `auto_awesome` |
| Section: Progress | 📊 | `analytics` | `analytics` |
| Section: Fields | 📋 | `checklist` | `checklist` |
| Field filled | ✅ | `check_circle` (filled, green) | `check_circle` |
| Field missing | ⭕ | `radio_button_unchecked` | `radio_button_unchecked` |
| Field optional empty | ◻️ | `check_box_outline_blank` | `check_box_outline_blank` |
| Force Generate | 🚀 | `bolt` | `bolt` |
| Section: System | 🔧 | `monitoring` | `monitoring` |
| API Connected | 🟢 | `check_circle` (green) | `check_circle` |
| API Offline | 🔴 | `error` (red) | `error` |
| API Degraded | 🟡 | `warning` (yellow) | `warning` |
| Ollama offline | ⚠️ | `cloud_off` | `cloud_off` |

#### Header

| Lokasi | Sebelum | Sesudah | Icon Name |
|--------|---------|---------|-----------|
| Theme toggle popover | ⋮ | `more_vert` | `more_vert` |
| Theme: System | 🖥 | `desktop_windows` | `desktop_windows` |
| Theme: Dark | 🌙 | `dark_mode` | `dark_mode` |
| Theme: Light | ☀️ | `light_mode` | `light_mode` |

#### Tabs

| Lokasi | Sebelum | Sesudah | Icon Name |
|--------|---------|---------|-----------|
| Tab Chat | 💬 | `chat` | `chat` |
| Tab Gemini Direct | 🚀 | `auto_awesome` | `auto_awesome` |
| Tab From Document | 📄 | `upload_file` | `upload_file` |

#### Chat Area

| Lokasi | Sebelum | Sesudah | Icon Name |
|--------|---------|---------|-----------|
| Empty state icon | 👇 | `forum` (besar, muted) | `forum` |
| AI thinking spinner | 🤔 | `psychology` | `psychology` |
| Error message | ❌ | `error` | `error` |

#### TOR Preview

| Lokasi | Sebelum | Sesudah | Icon Name |
|--------|---------|---------|-----------|
| Success banner | ✅ | `task_alt` (green) | `task_alt` |
| Metadata expander | 📋 | `info` | `info` |
| Download MD | ⬇️ | `download` | `download` |
| Download PDF | ⬇️ | `picture_as_pdf` | `picture_as_pdf` |
| Escalation warning | ⚠️ | `warning` (amber) | `warning` |
| Generate ulang | 🔄 | `refresh` | `refresh` |

#### Gemini Direct Form

| Lokasi | Sebelum | Sesudah | Icon Name |
|--------|---------|---------|-----------|
| Section title | 🚀 | `auto_awesome` | `auto_awesome` |
| Submit button | 🚀 | `send` | `send` |
| Validation error | ❌ | `error` | `error` |

#### From Document Tab

| Lokasi | Sebelum | Sesudah | Icon Name |
|--------|---------|---------|-----------|
| Section title | 📄 | `upload_file` | `upload_file` |
| Generating spinner | 🔨 | `manufacturing` | `manufacturing` |

---

## 5. Component Design — Detail per File

### 5.1 `config.py` — Constants & Settings

**Tanggung jawab**: Menyimpan semua konstanta, konfigurasi, dan definisi statis.

```python
# streamlit_app/config.py

from pathlib import Path

# --- Paths ---
ROOT = Path(__file__).parent
THEME_FILE = ROOT / ".streamlit" / ".current_theme"
CSS_DIR = ROOT / "styles"

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
REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
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

# --- Theme ---
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

**Digunakan oleh**: Semua modul lain.

---

### 5.2 `state.py` — Session State Manager

**Tanggung jawab**: Satu tempat untuk semua session state initialization & mutation.

```python
# streamlit_app/state.py

import streamlit as st
from config import THEME_FILE


def init_session_state():
    """Initialize all session state keys dengan default values."""
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
    """Reset chat session state tanpa menghapus theme/mode preferences."""
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.current_state = {
        "status": "NEW", "turn_count": 0,
        "completeness_score": 0.0,
        "filled_fields": [], "missing_fields": [],
    }
    st.session_state.tor_document = None
    st.session_state.escalation_info = None
    st.session_state.direct_tor = None
    st.session_state.doc_tor = None


def _load_theme_pref() -> str:
    if THEME_FILE.exists():
        val = THEME_FILE.read_text().strip()
        if val in ("system", "dark", "light"):
            return val
    return "system"
```

**Digunakan oleh**: `app.py`, semua components.

---

### 5.3 `theme.py` — Theme Engine

**Tanggung jawab**: Apply dan switch theme. Menggunakan kombinasi `st._config.set_option()` + CSS class toggle.

```python
# streamlit_app/theme.py

import streamlit as st
from config import THEMES, THEME_FILE


def apply_saved_theme():
    """Apply theme from saved preference on startup."""
    mode = st.session_state.get("app_theme", "system")
    _apply_config(mode)


def switch_theme(new_mode: str):
    """Switch theme, save preference, and rerun."""
    st.session_state.app_theme = new_mode
    THEME_FILE.write_text(new_mode)
    _apply_config(new_mode)
    st.rerun()


def _apply_config(mode: str):
    """Apply theme via st._config for BaseWeb components."""
    if mode in THEMES:
        for key, value in THEMES[mode].items():
            try:
                st._config.set_option(f"theme.{key}", value)
            except Exception:
                pass
    else:
        # system: clear overrides
        for key in ["base", "primaryColor", "backgroundColor",
                    "secondaryBackgroundColor", "textColor"]:
            try:
                st._config.set_option(f"theme.{key}", "")
            except Exception:
                pass


def get_current_theme() -> str:
    return st.session_state.get("app_theme", "system")
```

**Digunakan oleh**: `app.py`, `components/header.py`.

---

### 5.4 `api/client.py` — API Client

**Tanggung jawab**: Semua HTTP calls ke FastAPI backend. Satu-satunya modul yang import `requests`.

```python
# streamlit_app/api/client.py

import requests
import streamlit as st
from config import API_URL


def send_message(session_id, message, options=None) -> dict:
    """Send chat message ke hybrid endpoint."""
    ...

def check_health() -> dict:
    """Health check API backend."""
    ...

@st.cache_data(ttl=30)
def fetch_models() -> list[dict]:
    """Fetch available models."""
    ...

def force_generate(session_id) -> dict:
    """Force generate TOR dari session."""
    ...

def generate_direct(data: dict) -> dict:
    """Generate TOR langsung dari form data."""
    ...

def generate_from_document(file_bytes, filename, context="") -> dict:
    """Generate TOR dari uploaded document."""
    ...

def handle_response(data: dict) -> bool:
    """Process API response dan update session state."""
    ...
```

**Digunakan oleh**: `components/chat.py`, `components/form_direct.py`, `components/form_document.py`, `components/sidebar.py`.

---

### 5.5 `components/sidebar.py`

**Tanggung jawab**: Render seluruh sidebar — brand, new chat, model selector, progress, fields, force generate, system status.

```python
# streamlit_app/components/sidebar.py

import streamlit as st
from utils.icons import mi, mi_inline
from state import reset_session
from api.client import fetch_models, check_health, force_generate, handle_response
from config import REQUIRED_FIELDS, OPTIONAL_FIELDS, FIELD_LABELS


def render_sidebar():
    with st.sidebar:
        # Brand
        st.markdown(
            mi_inline("smart_toy", "TOR Generator", 24, gap=8),
            unsafe_allow_html=True,
        )

        # New Chat
        if st.button(mi_inline("add_comment", "Obrolan baru"), ...):
            reset_session()
            st.rerun()

        st.divider()

        # --- Model Selector ---
        _render_model_selector()

        st.divider()

        # --- Progress ---
        _render_progress()

        # --- Fields ---
        _render_fields_checklist()

        # --- Force Generate ---
        _render_force_generate()

        st.divider()

        # --- System Status ---
        _render_system_status()
```

**Input**: Tidak ada parameter — membaca langsung dari `st.session_state`.
**Output**: Renders sidebar DOM.

---

### 5.6 `components/header.py`

**Tanggung jawab**: Header area dengan judul dan theme toggle popover.

```python
# streamlit_app/components/header.py

import streamlit as st
from utils.icons import mi, mi_inline
from theme import switch_theme, get_current_theme


def render_header():
    col_title, col_menu = st.columns([9, 1])

    with col_title:
        mode = st.session_state.get("chat_mode", "local")
        label = "Gemini" if mode == "gemini" else "Local"
        icon = "auto_awesome" if mode == "gemini" else "computer"
        st.markdown(
            f'<h3 style="margin:0;">'
            f'{mi(icon, 24)} TOR Generator · {label}'
            f'</h3>',
            unsafe_allow_html=True,
        )

    with col_menu:
        _render_theme_popover()


def _render_theme_popover():
    current = get_current_theme()
    options = {
        "desktop_windows": ("Ikuti Sistem", "system"),
        "dark_mode": ("Gelap", "dark"),
        "light_mode": ("Terang", "light"),
    }

    with st.popover(mi("more_vert", 20)):
        st.caption("Tampilan")
        labels = [f"{mi(icon, 18)} {text}" for icon, (text, _) in options.items()]
        # ... radio selection + switch_theme() ...
```

**Input**: Tidak ada.
**Output**: Renders header + popover.

---

### 5.7 `components/chat.py`

**Tanggung jawab**: Tab chat — empty state, message list, TOR preview, chat input.

```python
# streamlit_app/components/chat.py

import streamlit as st
from utils.icons import mi
from api.client import send_message, handle_response
from components.tor_preview import render_tor_preview


def render_chat_tab():
    # Empty state
    if not st.session_state.messages and not st.session_state.tor_document:
        _render_empty_state()

    # Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # TOR Preview
    if st.session_state.tor_document:
        render_tor_preview(
            st.session_state.tor_document,
            st.session_state.escalation_info,
            key_suffix="_hybrid",
        )

    # Chat input
    if prompt := st.chat_input("Tanyakan apa saja..."):
        _handle_user_input(prompt)


def _render_empty_state():
    """Render empty state dengan Material Icon besar dan pesan terarah."""
    st.markdown(
        f'''
        <div style="text-align:center; padding:80px 20px; opacity:0.4;">
            {mi("forum", 64)}
            <h3 style="margin-top:16px;">Ceritakan kebutuhan TOR Anda</h3>
            <p style="font-size:14px;">Mulai chat untuk menyusun Term of Reference<br>
            dengan bantuan AI secara interaktif.</p>
        </div>
        ''',
        unsafe_allow_html=True,
    )
```

**Input**: Tidak ada parameter.
**Output**: Renders chat tab.

---

### 5.8 `components/tor_preview.py`

**Tanggung jawab**: Komponen reusable untuk menampilkan TOR yang sudah di-generate — dipakai di ketiga tab.

```python
# streamlit_app/components/tor_preview.py

import streamlit as st
from utils.icons import mi, mi_inline
from utils.formatters import export_to_pdf


def render_tor_preview(tor: dict, escalation_info=None, key_suffix=""):
    """Render TOR preview dengan metadata, content, download buttons, dan escalation warning."""

    st.divider()

    # Success banner
    st.markdown(
        f'<div style="...">{mi("task_alt", 24, "var(--color-success)")} '
        f'TOR Berhasil Dibuat</div>',
        unsafe_allow_html=True,
    )

    # Metadata
    with st.expander(mi_inline("info", "Metadata"), expanded=False):
        meta = tor.get("metadata", {})
        c = st.columns(4)
        c[0].metric("Model", meta.get("generated_by", "—"))
        c[1].metric("Mode", meta.get("mode", "—"))
        c[2].metric("Kata", meta.get("word_count", 0))
        c[3].metric("Waktu", f'{meta.get("generation_time_ms", 0)}ms')

    # Content
    st.markdown(tor["content"])

    # Download buttons
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            mi_inline("download", "Download .md"),
            tor["content"], f"tor{key_suffix}.md",
            "text/markdown", use_container_width=True,
            key=f"dl_md{key_suffix}",
        )
    with c2:
        pdf = export_to_pdf(tor["content"])
        st.download_button(
            mi_inline("picture_as_pdf", "Download .pdf"),
            pdf, f"tor{key_suffix}.pdf",
            "application/pdf", use_container_width=True,
            key=f"dl_pdf{key_suffix}", disabled=not pdf,
        )

    # Escalation warning
    if escalation_info:
        st.markdown(
            f'<div style="...">'
            f'{mi("warning", 20, "var(--color-warning)")} '
            f'TOR via eskalasi — {escalation_info.get("reason", "")}'
            f'</div>',
            unsafe_allow_html=True,
        )
```

**Input**: `tor: dict`, `escalation_info: dict | None`, `key_suffix: str`.
**Output**: Renders TOR document preview.
**Digunakan oleh**: `chat.py`, `form_direct.py`, `form_document.py`.

---

### 5.9 `components/form_direct.py`

**Tanggung jawab**: Tab Gemini Direct — form input dan generate TOR.

```python
# streamlit_app/components/form_direct.py

import streamlit as st
from utils.icons import mi_inline
from api.client import generate_direct
from components.tor_preview import render_tor_preview
from config import FIELD_LABELS


def render_direct_tab():
    st.markdown(
        f"### {mi_inline('auto_awesome', 'Generate TOR Langsung')}",
        unsafe_allow_html=True,
    )
    st.caption("Isi field, Gemini langsung membuat TOR tanpa proses chat.")

    with st.form("gemini_direct_form"):
        judul = st.text_input(
            f"{FIELD_LABELS['judul']} *",
            placeholder="Workshop Penerapan AI untuk ASN",
        )
        # ... more fields ...
        submitted = st.form_submit_button(
            mi_inline("send", "Generate TOR"),
            use_container_width=True,
        )

    if submitted:
        _handle_submit(...)

    if st.session_state.direct_tor:
        render_tor_preview(st.session_state.direct_tor, key_suffix="_direct")
        if st.button(mi_inline("refresh", "Generate Ulang"), key="reset_direct"):
            st.session_state.direct_tor = None
            st.rerun()
```

---

### 5.10 `components/form_document.py`

**Tanggung jawab**: Tab upload dokumen — file uploader dan generate TOR.

Analog dengan `form_direct.py` tapi menggunakan `st.file_uploader()`.

---

### 5.11 `utils/formatters.py`

**Tanggung jawab**: Pure utility functions — PDF export, text formatting.

```python
# streamlit_app/utils/formatters.py

import io
import markdown
from xhtml2pdf import pisa


def export_to_pdf(md_text: str) -> bytes:
    """Convert markdown → PDF bytes."""
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    styled = f"""<html><head><style>
        body {{ font-family: 'Inter', Helvetica, sans-serif; ... }}
    </style></head><body>{html}</body></html>"""
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled), dest=result)
    return b"" if pisa_status.err else result.getvalue()
```

---

### 5.12 `styles/loader.py`

**Tanggung jawab**: Inject semua CSS + font links ke Streamlit page.

```python
# streamlit_app/styles/loader.py

import streamlit as st
from pathlib import Path

STYLES_DIR = Path(__file__).parent


def inject_styles():
    """Inject all CSS + Google Fonts + Material Icons ke halaman."""
    base_css = (STYLES_DIR / "base.css").read_text()
    components_css = (STYLES_DIR / "components.css").read_text()

    st.markdown(f"""
    <!-- Google Fonts: Inter + JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

    <!-- Material Symbols (Outlined) -->
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL@20..48,100..700,0..1" rel="stylesheet">

    <style>
    {base_css}
    {components_css}
    </style>
    """, unsafe_allow_html=True)
```

---

## 6. UX State Design

### 6.1 Definisi 5 States

Setiap area interaktif harus menangani 5 state berikut:

```
┌──────────────────────────────────────────────────────────┐
│  STATE MACHINE PER AREA INTERAKTIF                       │
│                                                          │
│  ┌─────────┐   user action   ┌──────────┐               │
│  │  EMPTY  │ ───────────────► │ LOADING  │               │
│  │  STATE  │                  │  STATE   │               │
│  └─────────┘                  └────┬─────┘               │
│                                    │                     │
│                          ┌─────────┼──────────┐          │
│                          ▼                     ▼          │
│                   ┌──────────┐          ┌──────────┐     │
│                   │ SUCCESS  │          │  ERROR   │     │
│                   │  STATE   │          │  STATE   │     │
│                   └──────────┘          └────┬─────┘     │
│                                              │           │
│                                     ┌────────▼────────┐  │
│                                     │ ESCALATION      │  │
│                                     │ WARNING STATE   │  │
│                                     └─────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Visual per State

#### Empty State (Chat belum dimulai)

```
┌─────────────────────────────────────────┐
│                                         │
│              [forum icon]               │  Material Icon: forum
│              64px, muted                │  opacity: 0.3
│                                         │
│      Ceritakan kebutuhan TOR Anda       │  Inter 600, 20px
│                                         │
│   Mulai chat untuk menyusun Term of     │  Inter 400, 14px
│   Reference dengan bantuan AI           │  opacity: 0.5
│   secara interaktif.                    │
│                                         │
│           ┌──────────────────┐          │
│           │ [edit] Mulai Chat │          │  Optional CTA button
│           └──────────────────┘          │
│                                         │
└─────────────────────────────────────────┘
```

#### Loading State (AI sedang memproses)

```
┌──────────────────────────────────────────┐
│  ┌────────────────────────────────────┐  │
│  │ 🧑 User                            │  │
│  │ Buatkan TOR workshop AI 3 hari...  │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ [psychology icon + spinner]         │  │   Material: psychology
│  │ AI sedang memproses permintaan...  │  │   dengan pulse animation
│  └────────────────────────────────────┘  │
│                                          │
└──────────────────────────────────────────┘
```

CSS animation untuk loading:
```css
@keyframes pulse-thinking {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.thinking-indicator {
  animation: pulse-thinking 1.5s ease-in-out infinite;
}
```

#### Error State (API error / offline)

```
┌──────────────────────────────────────────┐
│  ┌──────────────────────────────────┐    │
│  │ [error icon] Terjadi Kesalahan   │    │  Material: error (red)
│  │                                  │    │  background: var(--color-error)/10%
│  │ Backend tidak bisa dihubungi.    │    │  border-left: 3px solid error
│  │ Pastikan server berjalan di      │    │
│  │ port 8000.                       │    │
│  │                                  │    │
│  │ [refresh] Coba Lagi              │    │  Material: refresh
│  └──────────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘
```

#### Success State (TOR berhasil)

```
┌──────────────────────────────────────────┐
│  ┌──────────────────────────────────┐    │
│  │ [task_alt icon] TOR Berhasil     │    │  Material: task_alt (green)
│  │ Dibuat                           │    │  background: var(--color-success)/8%
│  └──────────────────────────────────┘    │
│                                          │
│  [info] Metadata  ▾                      │  Collapsible
│  ┌──────────────────────────────────┐    │
│  │ Model    │ Mode   │ Kata │ Waktu│    │
│  │ gemini.. │ std    │ 850  │ 3.2s │    │
│  └──────────────────────────────────┘    │
│                                          │
│  # TERM OF REFERENCE                    │
│  ## Workshop Penerapan AI...             │
│  ...                                     │
│                                          │
│  ┌───────────────┐ ┌───────────────┐     │
│  │[download] .md │ │[pdf] .pdf     │     │  Material: download, picture_as_pdf
│  └───────────────┘ └───────────────┘     │
│                                          │
└──────────────────────────────────────────┘
```

#### Escalation Warning

```
┌──────────────────────────────────────────┐
│  ┌──────────────────────────────────┐    │
│  │ [warning icon] TOR via Eskalasi  │    │  Material: warning (amber)
│  │                                  │    │  background: var(--color-warning)/8%
│  │ Alasan: Auto-escalation setelah  │    │  border-left: 3px solid warning
│  │ 8 turn tanpa progress.           │    │
│  │                                  │    │
│  │ Bagian bertanda [ASUMSI] bisa    │    │
│  │ Anda sesuaikan.                  │    │
│  └──────────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘
```

---

## 7. Component CSS (`components.css`)

### 7.1 Prinsip CSS

```
BOLEH di-override (custom elements):
├── Chat bubble (border-radius, spacing)
├── Custom HTML containers (.empty-state, .success-banner, etc.)
├── Sidebar labels (.sidebar-label)
├── Scrollbar
├── Download buttons visual

JANGAN override (native Streamlit):
├── Expander arrows/internals
├── Radio button internals
├── Form element colors
├── Tab underline colors
├── Selectbox dropdown
```

### 7.2 Component Styles

```css
/* === components.css === */

/* Hide branding */
#MainMenu, footer { visibility: hidden; }

/* Chat bubbles */
[data-testid="stChatMessage"] {
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-2);
  padding: var(--space-3) var(--space-4);
}

/* Sidebar section label */
.sidebar-label {
  font-family: var(--font-sans);
  font-size: var(--text-xs);
  font-weight: 700;
  letter-spacing: 0.08rem;
  text-transform: uppercase;
  color: var(--color-text-subtle);
  margin: var(--space-4) 0 var(--space-2) 0;
}

/* Empty state container */
.empty-state {
  text-align: center;
  padding: var(--space-8) var(--space-5);
  color: var(--color-text-muted);
}
.empty-state h3 {
  font-family: var(--font-sans);
  font-weight: 600;
  margin-top: var(--space-4);
  color: var(--color-text-muted);
}
.empty-state p {
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--color-text-subtle);
}

/* Status banners */
.banner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: 500;
  margin: var(--space-3) 0;
}
.banner-success {
  background: color-mix(in srgb, var(--color-success) 10%, transparent);
  border-left: 3px solid var(--color-success);
  color: var(--color-success);
}
.banner-error {
  background: color-mix(in srgb, var(--color-error) 10%, transparent);
  border-left: 3px solid var(--color-error);
  color: var(--color-error);
}
.banner-warning {
  background: color-mix(in srgb, var(--color-warning) 10%, transparent);
  border-left: 3px solid var(--color-warning);
  color: var(--color-warning);
}
.banner-info {
  background: color-mix(in srgb, var(--color-info) 10%, transparent);
  border-left: 3px solid var(--color-info);
  color: var(--color-info);
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  border-radius: 3px;
  background: var(--color-border);
}

/* Download buttons */
.stDownloadButton button {
  border-radius: var(--radius-md) !important;
}

/* Thinking animation */
@keyframes pulse-thinking {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
.thinking-indicator {
  animation: pulse-thinking 1.5s ease-in-out infinite;
}

/* Material icon alignment fix */
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}
```

---

## 8. Mode UI — Tabs

### 8.1 Tab Layout

```
┌────────────────────────────────────────────────────────────────┐
│   [smart_toy] TOR Generator · [computer] Local        [⋮]    │
├────────────────────────────────────────────────────────────────┤
│   [chat] Chat    │  [auto_awesome] Gemini Direct  │  [upload] │
│═══════════════════                                            │
│                                                                │
│   ... active tab content ...                                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 8.2 UX per Tab

| Tab | Tujuan | User Journey | Input | Output |
|-----|--------|--------------|-------|--------|
| **Chat** | Wawancara interaktif | chat multi-turn → AI tanya → user jawab → auto-generate | Pesan teks | TOR markdown/PDF |
| **Gemini Direct** | Generate cepat dari form | Isi form 7 field → klik Generate → langsung jadi | Structured form | TOR markdown/PDF |
| **Dari Dokumen** | Generate dari dokumen sumber | Upload file → (opsional) konteks → Generate | File + teks | TOR markdown/PDF |

### 8.3 Transisi antar Tab

- Tab state **tidak berbagi** — setiap tab punya TOR result sendiri (`tor_document`, `direct_tor`, `doc_tor`)
- Chat session **persist** saat tab switching (karena pakai `st.session_state`)
- Reset hanya via tombol "Obrolan baru" di sidebar

---

## 9. Runbook Migrasi

### 9.1 Langkah-langkah migrasi dari monolit ke modular

```
Phase 1: Scaffold
  1. mkdir streamlit_app/
  2. Buat semua __init__.py
  3. Buat config.py, state.py (extract dari streamlit_app.py)

Phase 2: Extract Utils
  4. Pindahkan export_to_pdf → utils/formatters.py
  5. Buat utils/icons.py (Material Icons helper)
  6. Buat styles/base.css + components.css + loader.py

Phase 3: Extract API
  7. Pindahkan semua API functions → api/client.py

Phase 4: Extract Components
  8.  Buat components/sidebar.py (extract sidebar code)
  9.  Buat components/header.py (extract header + theme toggle)
  10. Buat components/chat.py (extract chat tab)
  11. Buat components/form_direct.py (extract Gemini Direct tab)
  12. Buat components/form_document.py (extract From Document tab)
  13. Buat components/tor_preview.py (extract render_tor_preview)

Phase 5: Create Entry Point
  14. Buat app.py sebagai orchestrator
  15. Update how_to_run.md: `streamlit run streamlit_app/app.py`

Phase 6: Theme & Polish
  16. Buat theme.py
  17. Replace semua emoji dengan Material Icons
  18. Polish CSS (empty state, banners, transitions)

Phase 7: Testing & Cleanup
  19. Test semua tabs berfungsi
  20. Test theme switching
  21. Delete streamlit_app.py (monolit lama)
  22. Update .gitignore, how_to_run.md
```

### 9.2 Backward Compatibility

- Streamlit command berubah dari `streamlit run streamlit_app.py` → `streamlit run streamlit_app/app.py`
- `.streamlit/config.toml` tetap di root project (bukan di `streamlit_app/`)
- `.streamlit/.current_theme` tetap di root project

---

## 10. Hubungan dengan Modul Sebelumnya

```
Beta 0.1.0: Chat Engine (Ollama)          ← UNCHANGED
Beta 0.1.2: Gemini Generator              ← UNCHANGED
Beta 0.1.3: RAG Pipeline                  ← UNCHANGED
Beta 0.1.4: Decision Engine               ← UNCHANGED
Beta 0.1.5: Streamlit UI                  ← REPLACED by 0.1.8
Beta 0.1.6: Document-to-TOR              ← PRESERVED (tab)
Beta 0.1.7: Chat UI + Model Select        ← SUPERSEDED by 0.1.8
Beta 0.1.8: THIS — Total UI Redesign
```

Backend **tidak berubah sama sekali** — beta 0.1.8 hanya menyentuh frontend Streamlit.

---

## 11. Task Breakdown

| # | File | Estimasi | Deskripsi | Dependencies |
|---|------|----------|-----------|--------------|
| 1 | `task01-scaffold-architecture.md` | Low | Folder structure + `__init__.py` + `config.py` + `state.py` | — |
| 2 | `task02-design-system-css.md` | Medium | `base.css` + `components.css` + `loader.py` | Task 01 |
| 3 | `task03-material-icons-helper.md` | Low | `utils/icons.py` — `mi()`, `mi_inline()`, `banner_html()` | Task 01, 02 |
| 4 | `task04-api-client-extract.md` | Low | Extract 7 API functions → `api/client.py` | Task 01 |
| 5 | `task05-theme-engine.md` | Medium | `theme.py` — apply, switch, persist | Task 01 |
| 6 | `task06-component-tor-preview.md` | Medium | `tor_preview.py` + `formatters.py` (reusable, dipakai 3 tab) | Task 01, 02, 03 |
| 7 | `task07-component-sidebar.md` | Medium | `sidebar.py` — brand, model selector, progress, fields, system | Task 01, 03, 04 |
| 8 | `task08-component-header.md` | Low | `header.py` — title + theme toggle popover | Task 01, 03, 05 |
| 9 | `task09-component-chat.md` | Medium | `chat.py` — empty state, messages, TOR preview, input | Task 01, 03, 04, 06 |
| 10 | `task10-component-form-direct.md` | Low | `form_direct.py` — structured form generate | Task 01, 03, 04, 06 |
| 11 | `task11-component-form-document.md` | Low | `form_document.py` — file upload generate | Task 01, 03, 04, 06 |
| 12 | `task12-entry-point-assembly.md` | Medium | `app.py` orchestrator + integration test | Task 01–11 |
| 13 | `task13-cleanup-migration.md` | Low | Delete monolit, update docs, final QA | Task 12 |

### Dependency Graph

```
Phase 1: Foundation (parallelizable)
  Task 01 (scaffold) ─┬─► Task 02 (CSS) ──► Task 03 (icons)
                       ├─► Task 04 (API client)
                       └─► Task 05 (theme engine)

Phase 2: Reusable Components
  Task 03 + 04 ────────────► Task 06 (TOR preview)

Phase 3: Page Components (parallelizable after Task 06)
  Task 06 ─┬─► Task 07 (sidebar)
            ├─► Task 08 (header)  ◄── Task 05
            ├─► Task 09 (chat)
            ├─► Task 10 (form direct)
            └─► Task 11 (form document)

Phase 4: Integration
  Task 07-11 ──────────────► Task 12 (entry point)

Phase 5: Cleanup
  Task 12 ─────────────────► Task 13 (cleanup)
```

> ✅ **Semua 13 task files telah dibuat** di folder `plan/beta0.1.8-ui-redesign/`.

---

## 12. Batasan & Catatan Penting

| Item | Detail |
|------|--------|
| **Material Icons = CDN dependency** | Icon require internet (Google Fonts CDN). Offline fallback: text label tanpa icon |
| **`st._config` = private API** | Theme engine masih pakai private API. Monitor jika Streamlit update breaking. Fallback: CSS variable only |
| **Streamlit render limitations** | `st.markdown(unsafe_allow_html=True)` dibutuhkan untuk semua custom HTML. Ini by-design. |
| **Tab labels** | Streamlit `st.tabs()` **tidak mendukung HTML** di label — icon di tab hanya bisa via emoji atau text. Workaround: CSS pseudo-element injection |
| **Performance** | Google Fonts + Material Symbols = ~2 HTTP request tambahan saat load. Gunakan `display=swap` untuk menghindari FOIT. |

---

> **Modul ini mentransformasi UI dari prototype monolitik menjadi aplikasi modular production-ready dengan design system konsisten, Material Icons, dan UX states yang profesional — tanpa mengubah backend API apapun.**
