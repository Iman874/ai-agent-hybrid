# Task 04: Header Simplify — Hapus Theme Popover, Material Icon Only

## 1. Judul Task

Simplifikasi header — hanya teks "Generator TOR" + icon Material Design

## 2. Deskripsi

Menghapus theme popover/toggle dan label provider dari header. Header menjadi minimal: hanya brand name + icon. Theme pindah ke Settings dialog (task 05).

## 3. Tujuan Teknis

- Hapus `_render_theme_popover()` atau toggle theme dari header
- Hapus label provider ("Local"/"Gemini") jika masih ada
- Header hanya: `mi("smart_toy")` + "Generator TOR"

## 4. Scope

**Yang dikerjakan:**
- `streamlit_app/components/header.py`

**Yang tidak dikerjakan:**
- Settings dialog (task 05)
- Sidebar (task 02)

## 5. Langkah Implementasi

### 5.1 Rewrite `render_header()`

**Sebelum** (header.py saat ini mengandung theme toggle dan/atau label provider):

```python
# Ada _render_theme_popover(), toggle, label, dll.
```

**Sesudah:**

```python
# streamlit_app/components/header.py
"""Header — minimal brand bar."""

import streamlit as st
from utils.icons import mi


def render_header():
    """Render top bar — brand name + icon, nothing else."""
    icon = mi("smart_toy", 20, "var(--color-primary)")
    st.markdown(
        f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
        f'{icon} Generator TOR</h3>',
        unsafe_allow_html=True,
    )
```

### 5.2 Hapus Import yang Tidak Dipakai

Hapus import `theme.py` functions, `switch_theme`, `get_current_theme` dll. dari header jika ada.

## 6. Output yang Diharapkan

Top bar:
```
[smart_toy] Generator TOR
```

- Tidak ada theme toggle
- Tidak ada label provider
- Tidak ada popover

## 7. Dependencies

Tidak ada dependency langsung (bisa dikerjakan paralel dengan task 02)

## 8. Acceptance Criteria

- [ ] Header hanya menampilkan icon `smart_toy` + teks "Generator TOR"
- [ ] Tidak ada theme toggle/popover di header
- [ ] Tidak ada label provider di header
- [ ] Icon pakai `mi("smart_toy")` — bukan emoji
- [ ] Server start tanpa error

## 9. Estimasi

Low (15 menit)
