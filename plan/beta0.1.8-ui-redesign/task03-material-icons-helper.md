# Task 03: Material Icons Helper — `utils/icons.py`

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat helper functions untuk Material Symbols (Google Icons).

## 2. Deskripsi

Buat modul `utils/icons.py` yang menyediakan fungsi-fungsi helper untuk
merender Material Symbols sebagai inline HTML. Modul ini akan digunakan
oleh SEMUA komponen sebagai pengganti emoji.

## 3. Tujuan Teknis

- Buat fungsi `mi(name, size, color, filled)` — render single icon
- Buat fungsi `mi_inline(name, text, size, gap)` — render icon + teks sejajar
- Buat fungsi `banner_html(icon, text, variant)` — render status banner
- Semua output berupa HTML string yang kompatibel dengan `st.markdown(unsafe_allow_html=True)`

## 4. Scope

**Yang dikerjakan:**
- `utils/icons.py` — 3 fungsi helper
- Semua fungsi return string HTML, bukan render Streamlit langsung

**Yang TIDAK dikerjakan:**
- Belum mengganti emoji di komponen (itu di Task 06-11)
- Belum membuat komponen UI apapun

## 5. Langkah Implementasi

### Step 1: Buat `utils/icons.py`

```python
# streamlit_app/utils/icons.py
"""Material Symbols helper functions.

Semua fungsi menghasilkan HTML string untuk digunakan dengan
st.markdown(..., unsafe_allow_html=True).

Referensi icon: https://fonts.google.com/icons
Font family: Material Symbols Outlined
"""


def mi(
    name: str,
    size: int = 20,
    color: str | None = None,
    filled: bool = False,
) -> str:
    """Render Material Symbol icon sebagai inline HTML <span>.

    Args:
        name: Nama icon (e.g. "chat", "auto_awesome", "check_circle")
        size: Ukuran font dalam pixel (default: 20)
        color: CSS color value (e.g. "#3fb950", "var(--color-success)")
        filled: Jika True, icon ditampilkan dengan fill solid

    Returns:
        HTML string: <span class="material-symbols-outlined" ...>name</span>

    Example:
        >>> mi("check_circle", 24, "var(--color-success)", filled=True)
        '<span class="material-symbols-outlined" style="font-size:24px;...">check_circle</span>'
    """
    style_parts = [f"font-size:{size}px", "vertical-align:middle"]
    if color:
        style_parts.append(f"color:{color}")
    if filled:
        style_parts.append("font-variation-settings:'FILL' 1")
    style = ";".join(style_parts)
    return f'<span class="material-symbols-outlined" style="{style}">{name}</span>'


def mi_inline(
    name: str,
    text: str,
    size: int = 20,
    gap: int = 6,
    color: str | None = None,
    filled: bool = False,
) -> str:
    """Render Material Icon + teks dalam satu baris inline-flex.

    Args:
        name: Nama icon Material Symbol
        text: Teks yang ditampilkan di samping icon
        size: Ukuran icon (px)
        gap: Jarak antara icon dan teks (px)
        color: Warna icon (CSS value)
        filled: Icon filled atau outlined

    Returns:
        HTML string dengan flex container

    Example:
        >>> mi_inline("smart_toy", "TOR Generator", 24)
        '<span style="display:inline-flex;..."><span ...>smart_toy</span> TOR Generator</span>'
    """
    icon = mi(name, size, color, filled)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{gap}px;">'
        f'{icon} {text}'
        f'</span>'
    )


def banner_html(
    icon: str,
    text: str,
    variant: str = "info",
    icon_size: int = 20,
) -> str:
    """Render status banner HTML (success/error/warning/info).

    Menggunakan CSS class dari components.css: .banner + .banner-{variant}

    Args:
        icon: Nama Material Symbol (e.g. "task_alt", "error", "warning")
        text: Pesan yang ditampilkan
        variant: "success" | "error" | "warning" | "info"
        icon_size: Ukuran icon (px)

    Returns:
        HTML string dengan class .banner .banner-{variant}

    Example:
        >>> banner_html("task_alt", "TOR Berhasil Dibuat!", "success")
        '<div class="banner banner-success">...<span...>task_alt</span> TOR Berhasil Dibuat!</div>'
    """
    color_map = {
        "success": "var(--color-success)",
        "error": "var(--color-error)",
        "warning": "var(--color-warning)",
        "info": "var(--color-info)",
    }
    icon_color = color_map.get(variant, color_map["info"])
    icon_html = mi(icon, icon_size, icon_color, filled=True)
    return f'<div class="banner banner-{variant}">{icon_html} {text}</div>'
```

### Step 2: Update `app.py` untuk test

```python
# Di app.py:
from utils.icons import mi, mi_inline, banner_html

# Test icon rendering
st.markdown(mi("smart_toy", 48, "var(--color-primary)"), unsafe_allow_html=True)
st.markdown(mi_inline("chat", "Chat Mode", 20), unsafe_allow_html=True)
st.markdown(mi_inline("auto_awesome", "Gemini Direct", 20), unsafe_allow_html=True)
st.markdown(mi_inline("upload_file", "Dari Dokumen", 20), unsafe_allow_html=True)

# Test banners
st.markdown(banner_html("task_alt", "TOR Berhasil Dibuat!", "success"), unsafe_allow_html=True)
st.markdown(banner_html("error", "Backend offline", "error"), unsafe_allow_html=True)
st.markdown(banner_html("warning", "Data kurang lengkap", "warning"), unsafe_allow_html=True)
st.markdown(banner_html("info", "Menggunakan Gemini API", "info"), unsafe_allow_html=True)
```

### Step 3: Verifikasi visual

- Icon Material Symbols tampil dengan benar
- Warna sesuai CSS variables
- Alignment icon + text sejajar (tidak naik/turun)
- Banner memiliki background + border-left yang benar

## 6. Output yang Diharapkan

```
streamlit_app/utils/
├── __init__.py
├── icons.py         (~100 lines — 3 fungsi)
└── formatters.py    (belum, Task berikutnya)
```

Fungsi siap dipakai:
```python
mi("chat")                                    # → <span...>chat</span>
mi("check_circle", 24, "#3fb950", filled=True) # → filled green icon
mi_inline("smart_toy", "TOR Generator", 24)    # → icon + text inline
banner_html("task_alt", "Berhasil!", "success") # → green banner
```

## 7. Dependencies

- **Task 01** — folder `utils/` harus ada
- **Task 02** — Material Symbols font harus sudah di-inject oleh `loader.py`

## 8. Acceptance Criteria

- [ ] `mi()` menghasilkan `<span class="material-symbols-outlined">` yang valid
- [ ] `mi(filled=True)` menambahkan `font-variation-settings:'FILL' 1`
- [ ] `mi_inline()` menampilkan icon + text sejajar via inline-flex
- [ ] `banner_html()` menghasilkan div dengan class `.banner .banner-{variant}`
- [ ] Semua icon Material Symbols render dengan benar di browser
- [ ] Icon alignment tidak terdistorsi (vertical-align: middle)

## 9. Estimasi

**Low** — Pure functions, tidak ada state management.
