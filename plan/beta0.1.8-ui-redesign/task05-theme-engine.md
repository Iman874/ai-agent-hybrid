# Task 05: Theme Engine — `theme.py`

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat theme engine stabil yang mendukung 3 mode (System / Dark / Light).

## 2. Deskripsi

Buat modul `theme.py` yang mengelola tema aplikasi. Modul ini menangani:
- Apply theme saat startup dari saved preference
- Switch theme saat runtime via `st._config.set_option()` + `st.rerun()`
- Persist pilihan ke file `.current_theme`

## 3. Tujuan Teknis

- `apply_saved_theme()` — dipanggil di `app.py` saat startup
- `switch_theme(mode)` — dipanggil saat user ganti tema
- `get_current_theme()` — getter untuk state saat ini
- Tema persisten setelah restart Streamlit

## 4. Scope

**Yang dikerjakan:**
- `theme.py` — apply, switch, persist logic
- Menggunakan `st._config.set_option()` untuk BaseWeb compatibility

**Yang TIDAK dikerjakan:**
- UI popover (itu di `components/header.py`, Task 08)
- CSS variables toggle (sudah di `base.css`, Task 02)

## 5. Langkah Implementasi

### Step 1: Buat `theme.py`

```python
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
```

### Step 2: Update `app.py`

```python
from theme import apply_saved_theme

# Setelah init_session_state()
apply_saved_theme()
```

### Step 3: Test manual

```python
# Di app.py sementara:
from theme import switch_theme, get_current_theme

st.write(f"Current theme: {get_current_theme()}")
c1, c2, c3 = st.columns(3)
if c1.button("System"):
    switch_theme("system")
if c2.button("Dark"):
    switch_theme("dark")
if c3.button("Light"):
    switch_theme("light")
```

Verifikasi:
- Klik "Light" → halaman rerun + warna berubah
- Klik "Dark" → balik ke dark
- Restart Streamlit → pilihan terakhir tetap berlaku

## 6. Output yang Diharapkan

```
streamlit_app/
├── theme.py     (~65 lines)
```

File `.streamlit/.current_theme` berisi string: "system", "dark", atau "light".

## 7. Dependencies

- **Task 01** — `config.py` harus berisi `THEMES` dan `THEME_FILE`
- **Task 01** — `state.py` harus init `app_theme` dari `_load_theme_pref()`

## 8. Acceptance Criteria

- [ ] `apply_saved_theme()` berjalan tanpa error saat cold start
- [ ] `switch_theme("light")` → halaman rerun + warna berubah ke light
- [ ] `switch_theme("dark")` → halaman rerun + warna berubah ke dark
- [ ] `switch_theme("system")` → clear overrides
- [ ] Pilihan theme persisten setelah restart Streamlit
- [ ] File `.streamlit/.current_theme` ter-update setiap switch
- [ ] `get_current_theme()` return nilai yang benar

## 9. Estimasi

**Medium** — Logic sederhana tapi harus handle edge cases `_config`.
