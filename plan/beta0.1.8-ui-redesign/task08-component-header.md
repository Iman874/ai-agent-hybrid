# Task 08: Component — Header + Theme Toggle (`components/header.py`)

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat header area dengan title dan theme toggle popover menggunakan Material Icons.

## 2. Deskripsi

Buat komponen header yang menampilkan judul "TOR Generator · {mode}" di kiri
dan tombol `⋮` (more_vert) di kanan. Popover berisi 3 opsi tema:
`desktop_windows` Ikuti Sistem, `dark_mode` Gelap, `light_mode` Terang.

## 3. Tujuan Teknis

- `render_header()` — render layout 2 kolom (title + popover)
- Theme toggle menggunakan `switch_theme()` dari `theme.py`
- Material Icons: `computer`, `auto_awesome`, `more_vert`, `desktop_windows`, `dark_mode`, `light_mode`

## 4. Scope

**Yang dikerjakan:**
- `components/header.py` — header + theme popover

**Yang TIDAK dikerjakan:**
- Theme logic (sudah di Task 05 `theme.py`)
- Sidebar (Task 07)

## 5. Langkah Implementasi

### Step 1: Buat `components/header.py`

```python
# streamlit_app/components/header.py
"""Header area — title bar + theme toggle popover."""

import streamlit as st
from utils.icons import mi
from theme import switch_theme, get_current_theme


def render_header():
    """Render header: title (left) + theme menu (right)."""
    col_title, col_menu = st.columns([9, 1])

    with col_title:
        mode = st.session_state.get("chat_mode", "local")
        if mode == "gemini":
            icon = mi("auto_awesome", 22, "var(--color-accent)")
            label = "Gemini"
        else:
            icon = mi("computer", 22, "var(--color-primary)")
            label = "Local"

        st.markdown(
            f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
            f'{icon} TOR Generator · {label}'
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
```

### Step 2: Update `app.py`

```python
from components.header import render_header
render_header()
```

### Step 3: Test

- Klik `⋮` → popover muncul dengan 3 opsi
- Pilih "Terang" → halaman rerun + tema berubah
- Pilih "Gelap" → kembali ke dark
- Pilih "Ikuti Sistem" → ikuti browser default

## 6. Output yang Diharapkan

```
streamlit_app/components/
├── header.py        (~60 lines)
```

## 7. Dependencies

- **Task 01** — config, state
- **Task 03** — `mi()`
- **Task 05** — `switch_theme()`, `get_current_theme()`

## 8. Acceptance Criteria

- [ ] Header menampilkan "TOR Generator · Local" atau "TOR Generator · Gemini"
- [ ] Icon berubah antara `computer` dan `auto_awesome` sesuai chat mode
- [ ] Tombol `⋮` di pojok kanan berfungsi (popover muncul)
- [ ] 3 opsi tema tersedia di popover
- [ ] Memilih tema baru → `switch_theme()` → halaman rerun + tema berubah
- [ ] Tidak crash saat theme switching

## 9. Estimasi

**Low** — Komponen kecil, logic delegasi ke `theme.py`.
