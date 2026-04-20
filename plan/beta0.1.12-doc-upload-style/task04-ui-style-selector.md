# Task 04: UI — Style Selector di Tab "Dari Dokumen"

> **Status**: [x] Selesai
> **Estimasi**: Medium (1–2 jam)
> **Dependency**: Task 03 (state + client harus ready)

## 1. Deskripsi

Menambahkan widget style selector di `form_document.py` sehingga user bisa memilih "Gunakan style aktif" atau memilih style lain dari dropdown, sebelum meng-generate TOR dari dokumen.

## 2. Tujuan Teknis

- Radio button untuk memilih mode: "style aktif" atau "pilih style lain"
- Dropdown `st.selectbox` menampilkan semua styles saat mode "pilih lain"
- `style_id` yang dipilih dikirim ke `generate_from_document()` via client

## 3. Scope

**Yang dikerjakan:**
- `streamlit_app/components/form_document.py` — tambah style selector UI
- Wire `style_id` ke `_handle_generate()`

**Yang tidak dikerjakan:**
- Auto-detect flow (task05)
- Backend perubahan (sudah selesai di task01-02)

## 4. Langkah Implementasi

### 4.1 Tambah Import

- [x] Tambahkan import di bagian atas `form_document.py`:

```diff
 from utils.icons import mi, banner_html
 from api.client import generate_from_document
+from api.client import get_styles, get_active_style
 from components.tor_preview import render_tor_preview
```

### 4.2 Tambah Style Selector Widget

- [x] Setelah `st.caption(...)` (line 21) dan sebelum `uploaded_file = st.file_uploader(...)` (line 23), tambahkan section style selector:

```python
    # --- Style Selection ---
    st.markdown("---")
    st.markdown(f"**{mi('palette', 18, 'var(--color-accent)')} Format Output TOR**", unsafe_allow_html=True)

    # Fetch active style name
    active = get_active_style()
    active_name = active.get("name", "Default") if active else "Default"

    style_mode = st.radio(
        "Pilih format output",
        options=["active", "choose"],
        format_func=lambda x: {
            "active": f"🎨 Pakai style aktif ({active_name})",
            "choose": "📋 Pilih style lain",
        }[x],
        horizontal=True,
        label_visibility="collapsed",
        key="doc_style_radio",
    )

    selected_style_id = None

    if style_mode == "choose":
        styles = get_styles()
        if styles:
            style_options = {s["id"]: f"{s['name']} {'✅' if s.get('is_active') else ''}" for s in styles}
            selected_style_id = st.selectbox(
                "Pilih style",
                options=list(style_options.keys()),
                format_func=lambda x: style_options[x],
                label_visibility="collapsed",
                key="doc_style_select",
            )
        else:
            st.caption("_Tidak ada style tersedia._")

    st.markdown("---")
```

### 4.3 Simpan Selected Style ID ke State

- [x] Setelah style selector, update state:

```python
    st.session_state.doc_selected_style_id = selected_style_id
```

### 4.4 Update `_handle_generate()` untuk Pass `style_id`

- [x] Ubah pemanggilan `_handle_generate()` dari:

```python
    if uploaded_file:
        _handle_generate(uploaded_file, doc_context)
```

Menjadi:

```python
    if uploaded_file:
        _handle_generate(uploaded_file, doc_context, selected_style_id)
```

- [x] Ubah signature `_handle_generate()`:

```python
def _handle_generate(uploaded_file, context: str, style_id: str | None = None):
    """Process uploaded file dan generate TOR."""
    with st.spinner("Membaca dokumen dan generating TOR..."):
        result = generate_from_document(
            uploaded_file.read(),
            uploaded_file.name,
            context,
            style_id=style_id,
        )

    if "error" in result:
        st.markdown(
            banner_html("error", result["error"], "error"),
            unsafe_allow_html=True,
        )
    else:
        st.session_state.doc_tor = result.get("tor_document", result)
        st.session_state.doc_session_id = result.get("session_id", "")
        st.rerun()
```

## 5. Output yang Diharapkan

### UI Layout (Setelah Implementasi):
```
### 📤 Generate TOR dari Dokumen
Upload dokumen sumber, Gemini otomatis membuat TOR.

────────────────────────────────────────
🎨 Format Output TOR

  ○ 🎨 Pakai style aktif (Format TOR Standar)
  ○ 📋 Pilih style lain

  [Jika "Pilih style lain":]
  ┌─▼ Template Pelatihan Resmi ────┐
  │ Format TOR Standar ✅           │
  │ Template Pelatihan Resmi        │
  │ Template Pengadaan Barang       │
  └─────────────────────────────────┘

────────────────────────────────────────

Upload dokumen: [Choose File]
Konteks tambahan: [__________]

[Generate TOR]
```

## 6. Acceptance Criteria

- [x] Style selector muncul di tab "Dari Dokumen".
- [x] Default: "Pakai style aktif" terpilih.
- [x] Memilih "Pilih style lain" → dropdown muncul dengan semua styles.
- [x] Generate dengan "style aktif" → `style_id=None` dikirim ke client.
- [x] Generate dengan style spesifik → `style_id` dikirim ke client.
- [x] Jika tidak ada styles (API down) → caption "Tidak ada style tersedia" muncul.
