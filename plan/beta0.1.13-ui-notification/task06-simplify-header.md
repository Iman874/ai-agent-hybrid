# Task 06: Simplify Header — Hapus Provider Label

> **Status**: [x] Selesai
> **Estimasi**: Low (15–30 menit)
> **Dependency**: Tidak ada (independen)

## 1. Deskripsi

Menghapus label provider ("Local" / "Gemini") dari header, karena provider selection akan pindah ke tab Chat (task 07). Header sekarang hanya menampilkan "TOR Generator" tanpa mention provider.

## 2. Tujuan Teknis

- Header tidak lagi menampilkan `· Local` / `· Gemini`
- `chat_mode` tidak lagi dibaca di `header.py`
- Icon header tetap `smart_toy` (Material Design)

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/header.py` — simplify render

**Yang tidak dikerjakan:**
- Model selector relocation (task 07)

## 4. Langkah Implementasi

### 4.1 Simplify `render_header()` (line 9-27)

- [x] Ubah dari:

```python
def render_header():
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
```

Menjadi:

```python
def render_header():
    col_title, col_menu = st.columns([9, 1])
    with col_title:
        icon = mi("smart_toy", 22, "var(--color-primary)")
        st.markdown(
            f'<h3 style="margin:0;display:flex;align-items:center;gap:8px;">'
            f'{icon} TOR Generator'
            f'</h3>',
            unsafe_allow_html=True,
        )
    with col_menu:
        _render_theme_popover()
```

## 5. Output yang Diharapkan

```
SEBELUM: 🤖 TOR Generator · Local     [⋮]
         ✨ TOR Generator · Gemini    [⋮]

SESUDAH: 🤖 TOR Generator             [⋮]
```

## 6. Acceptance Criteria

- [x] Header menampilkan `TOR Generator` tanpa label provider.
- [x] Icon header tetap konsisten (Material Design `smart_toy`).
- [x] `chat_mode` tidak lagi dibaca di `header.py`.
- [x] Theme popover masih berfungsi.
