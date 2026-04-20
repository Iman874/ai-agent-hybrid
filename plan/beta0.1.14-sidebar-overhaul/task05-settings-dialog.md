# Task 05: Settings Dialog — Tampilan / Format TOR / Bahasa

## 1. Judul Task

Buat file baru `settings_dialog.py` — modal dialog dengan tabs Tampilan, Format TOR, Bahasa

## 2. Deskripsi

Membuat dialog pengaturan yang menggantikan theme popover (dari header) dan tab "Format TOR" (dari area utama). Semua pengaturan terpusat di satu dialog yang dibuka dari tombol "Pengaturan" di sidebar.

## 3. Tujuan Teknis

- File baru: `streamlit_app/components/settings_dialog.py`
- `@st.dialog("Pengaturan", width="large")`
- 3 tabs DI DALAM dialog: Tampilan | Format TOR | Bahasa
- Tab Tampilan: radio theme (default sistem / gelap / terang)
- Tab Format TOR: konten dari `format_tab.py` yang direfactor
- Tab Bahasa: placeholder (fitur mendatang)

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/components/settings_dialog.py` — file baru
- `streamlit_app/components/format_tab.py` — expose `render_format_settings()` function
- `streamlit_app/components/sidebar.py` — update import `show_settings_dialog`

**Yang tidak dikerjakan:**
- Implementasi fitur bahasa (placeholder)
- Ubah logic format TOR (hanya pindah lokasi render)

## 5. Langkah Implementasi

### 5.1 Buat `settings_dialog.py`

```python
# streamlit_app/components/settings_dialog.py
"""Settings dialog — Tampilan, Format TOR, Bahasa."""

import streamlit as st
from theme import get_current_theme, switch_theme


@st.dialog("Pengaturan", width="large")
def show_settings_dialog():
    """Dialog pengaturan — tabs di dalam."""
    tab_theme, tab_format, tab_lang = st.tabs(["Tampilan", "Format TOR", "Bahasa"])

    with tab_theme:
        _render_theme_settings()

    with tab_format:
        _render_format_tor_settings()

    with tab_lang:
        _render_lang_settings()


def _render_theme_settings():
    """Pengaturan tema tampilan."""
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


def _render_format_tor_settings():
    """Konten format TOR — import dari format_tab.py."""
    try:
        from components.format_tab import render_format_settings
        render_format_settings()
    except ImportError:
        st.caption("_Pengaturan format TOR belum tersedia._")


def _render_lang_settings():
    """Pengaturan bahasa — placeholder."""
    st.radio(
        "Bahasa",
        ["Bahasa Indonesia", "English"],
        label_visibility="collapsed",
    )
    st.caption("Fitur bahasa akan tersedia di versi mendatang.")
```

### 5.2 Refactor `format_tab.py` — Expose Render Function

Di `format_tab.py`, pastikan ada fungsi yang bisa dipanggil dari luar:

```python
# Di format_tab.py, TAMBAHKAN alias:
def render_format_settings():
    """Render konten format TOR untuk digunakan di settings dialog."""
    # Panggil fungsi utama yang sudah ada
    # Wrap bagian advanced dalam st.expander()
    _render_style_list()    # existing function
    
    with st.expander("Pengaturan Lanjutan"):
        _render_extraction()  # existing function (jika ada)
```

Jika `format_tab.py` sudah punya `render_format_tab()`, cukup buat wrapper `render_format_settings()` yang memanggil konten internalnya tanpa tab wrapper.

### 5.3 Update Import di `sidebar.py`

```python
# sidebar.py — ganti placeholder show_settings_dialog
from components.settings_dialog import show_settings_dialog
```

Hapus placeholder function `show_settings_dialog()` yang dibuat di task 02.

## 6. Output yang Diharapkan

Dialog saat dibuka:

```
┌──────────────────────────────────────────┐
│ Pengaturan                          [✕]  │
│                                          │
│ [ Tampilan | Format TOR | Bahasa ]       │
│                                          │
│ Tema:                                    │
│   ○ Default sistem                       │
│   ● Gelap                                │
│   ○ Terang                               │
│                                          │
└──────────────────────────────────────────┘
```

## 7. Dependencies

- Task 02 (sidebar: tombol Pengaturan)
- `format_tab.py` harus sudah ada (sudah ada dari beta sebelumnya)
- `theme.py` harus sudah ada (sudah ada)

## 8. Acceptance Criteria

- [ ] File `settings_dialog.py` baru dibuat
- [ ] `@st.dialog` berfungsi — bisa dibuka dari tombol Pengaturan di sidebar
- [ ] 3 tabs: Tampilan, Format TOR, Bahasa
- [ ] Tab Tampilan: theme switch berfungsi (dark/light/system)
- [ ] Tab Format TOR: konten dari `format_tab.py` tampil
- [ ] Tab Bahasa: radio + caption placeholder
- [ ] Import di sidebar.py diupdate
- [ ] Server start tanpa error

## 9. Estimasi

Medium (1–2 jam)
