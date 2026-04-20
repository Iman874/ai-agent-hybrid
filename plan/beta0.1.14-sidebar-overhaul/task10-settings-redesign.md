# Task 10: Settings Redesign — ChatGPT-Style Sidebar Navigation

## 1. Judul Task

Redesign settings dialog dari tabs lebar menjadi ChatGPT-style sidebar navigasi

## 2. Deskripsi

Mengganti `st.tabs(["Tampilan", "Format TOR", "Bahasa"])` yang terlalu lebar dengan layout 2 kolom: sidebar navigasi kiri + konten kanan. Terinspirasi pengaturan ChatGPT yang menggunakan list navigasi vertikal.

## 3. Tujuan Teknis

- Layout: `st.columns([1, 3])` — nav kiri (25%), konten kanan (75%)
- 3 section navigasi: **Umum**, **Format TOR**, **Lanjutan**
- State `_settings_section` mengontrol section aktif
- Section Umum: tema + bahasa
- Section Format TOR: konten dari `format_tab.py`
- Section Lanjutan: API endpoint, cache, pengaturan developer

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/components/settings_dialog.py` — rewrite total
- Tambah `_settings_section` ke state defaults

**Yang tidak dikerjakan:**
- Logic format TOR (hanya lokasi render berubah)
- Backend pengaturan (ekspansi masa depan)
- Implementasi bahasa (placeholder)

## 5. Langkah Implementasi

### 5.1 Tambah State Default

Di `state.py`, tambah:
```python
"_settings_section": "umum",  # "umum" | "format_tor" | "lanjutan"
```

### 5.2 Rewrite `settings_dialog.py`

```python
# streamlit_app/components/settings_dialog.py
"""Settings dialog — ChatGPT-style sidebar navigation."""

import streamlit as st
from theme import get_current_theme, switch_theme
from utils.notify import notify


@st.dialog("Pengaturan", width="large")
def show_settings_dialog():
    """Dialog pengaturan dengan sidebar nav kiri + konten kanan."""
    col_nav, col_content = st.columns([1, 3])

    # --- Sidebar navigasi ---
    with col_nav:
        nav_items = {
            "umum": "Umum",
            "format_tor": "Format TOR",
            "lanjutan": "Lanjutan",
        }
        current_section = st.session_state.get("_settings_section", "umum")

        for key, label in nav_items.items():
            btn_type = "primary" if key == current_section else "secondary"
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state._settings_section = key
                st.rerun()

    # --- Konten ---
    with col_content:
        section = st.session_state.get("_settings_section", "umum")

        if section == "umum":
            _render_general_settings()
        elif section == "format_tor":
            _render_format_tor_settings()
        elif section == "lanjutan":
            _render_advanced_settings()
```

### 5.3 Section: Umum

```python
def _render_general_settings():
    """Section Umum — Tema + Bahasa."""
    st.markdown("#### Penampilan")
    current = get_current_theme()
    opts = {"system": "Default sistem", "dark": "Gelap", "light": "Terang"}
    selected = st.radio(
        "Tema",
        list(opts.keys()),
        format_func=lambda k: opts[k],
        index=list(opts.keys()).index(current),
        label_visibility="collapsed",
    )
    if selected != current:
        switch_theme(selected)

    st.divider()

    st.markdown("#### Bahasa")
    st.radio(
        "Bahasa", ["Bahasa Indonesia", "English"],
        label_visibility="collapsed",
    )
    st.caption("Fitur bahasa akan tersedia di versi mendatang.")
```

### 5.4 Section: Format TOR

```python
def _render_format_tor_settings():
    """Section Format TOR — style management."""
    st.markdown("#### Format TOR")
    try:
        from components.format_tab import render_format_settings
        render_format_settings()
    except ImportError:
        st.caption("_Pengaturan format TOR belum tersedia._")
```

### 5.5 Section: Lanjutan

```python
def _render_advanced_settings():
    """Section Lanjutan — pengaturan teknis."""
    st.markdown("#### Pengaturan Lanjutan")
    st.caption("Pengaturan teknis untuk developer.")

    with st.expander("API Endpoint"):
        st.code("http://localhost:8000/api/v1")

    with st.expander("Cache"):
        if st.button("Hapus Cache", key="clear_cache"):
            st.cache_data.clear()
            notify("Cache berhasil dihapus.", "success")
```

### 5.6 CSS untuk Navigasi Sidebar Dialog

Tambah di `components.css`:

```css
/* Settings dialog — sidebar nav buttons */
[data-testid="stDialog"] .stButton > button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    text-align: left !important;
    font-size: var(--text-sm) !important;
    color: var(--color-text-muted) !important;
    padding: var(--space-2) var(--space-3) !important;
    border-radius: var(--radius-md) !important;
}
[data-testid="stDialog"] .stButton > button[kind="secondary"]:hover {
    background: color-mix(in srgb, var(--color-text) 6%, transparent) !important;
}
[data-testid="stDialog"] .stButton > button[kind="primary"] {
    background: color-mix(in srgb, var(--color-primary) 12%, transparent) !important;
    border: none !important;
    text-align: left !important;
    font-size: var(--text-sm) !important;
    font-weight: 600 !important;
    border-radius: var(--radius-md) !important;
}
```

## 6. Output yang Diharapkan

```
┌────────────────────────────────────────────────┐
│ Pengaturan                                [✕]  │
│                                                │
│ ┌──────────┬─────────────────────────────────┐ │
│ │ ▌Umum    │  Penampilan                     │ │
│ │  Format  │    ○ Default sistem             │ │
│ │  Lanjutan│    ● Gelap                      │ │
│ │          │    ○ Terang                      │ │
│ │          │                                 │ │
│ │          │  ───────────                    │ │
│ │          │                                 │ │
│ │          │  Bahasa                         │ │
│ │          │    ● Bahasa Indonesia            │ │
│ │          │    ○ English                     │ │
│ └──────────┴─────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

## 7. Dependencies

- Task 05 (settings_dialog.py sudah ada — ini adalah redesign)
- `format_tab.py` sudah punya `render_format_settings()`

## 8. Acceptance Criteria

- [ ] Dialog dibuka → layout 2 kolom (nav kiri + konten kanan)
- [ ] Navigasi 3 item: Umum, Format TOR, Lanjutan
- [ ] Klik nav item → konten kanan berubah sesuai section
- [ ] Nav item aktif → highlight halus (primary button style)
- [ ] Section Umum: tema switch berfungsi
- [ ] Section Format TOR: konten dari `format_tab.py` tampil
- [ ] Section Lanjutan: expanders API + Cache berfungsi
- [ ] TIDAK ADA `st.tabs()` yang lebar di dialog
- [ ] Dialog tidak terlalu panjang / nyaman dibaca
- [ ] CSS settings nav consistent dengan sidebar nav style

## 9. Estimasi

Medium (1–2 jam)
