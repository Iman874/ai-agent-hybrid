# Task 11: Component — From Document Tab (`components/form_document.py`)

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat komponen tab From Document — upload file dan generate TOR.

## 2. Deskripsi

Extract tab From Document dari monolit ke `components/form_document.py`.
Tab ini menggunakan `st.file_uploader()` untuk upload dokumen sumber +
optional konteks tambahan, lalu generate TOR via API.

## 3. Tujuan Teknis

- `render_document_tab()` — entry function
- File uploader (PDF, TXT, MD, DOCX) + konteks opsional
- Generate button + spinner + TOR preview
- Tombol "Generate Ulang" untuk reset

## 4. Scope

**Yang dikerjakan:**
- `components/form_document.py` — file upload + generate

**Yang TIDAK dikerjakan:**
- API client (Task 04)
- TOR preview (Task 06)

## 5. Langkah Implementasi

### Step 1: Buat `components/form_document.py`

```python
# streamlit_app/components/form_document.py
"""From Document tab — generate TOR from uploaded document."""

import streamlit as st
from utils.icons import mi, banner_html
from api.client import generate_from_document
from components.tor_preview import render_tor_preview


def render_document_tab():
    """Render tab From Document: file upload + generate."""

    st.markdown(
        f"### {mi('upload_file', 24, 'var(--color-primary)')} Generate TOR dari Dokumen",
        unsafe_allow_html=True,
    )
    st.caption("Upload dokumen sumber, Gemini otomatis membuat TOR.")

    uploaded_file = st.file_uploader(
        "Upload dokumen",
        type=["pdf", "txt", "md", "docx"],
        help="Format: PDF, TXT, MD, DOCX. Maks 20MB.",
    )
    doc_context = st.text_area(
        "Konteks tambahan (opsional)",
        placeholder="Contoh: Ini lanjutan workshop tahun lalu...",
        height=100,
    )

    if st.button(
        "Generate TOR",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        if uploaded_file:
            _handle_generate(uploaded_file, doc_context)

    # Show result
    if st.session_state.doc_tor:
        render_tor_preview(st.session_state.doc_tor, key_suffix="_doc")
        if st.button("Generate Ulang", key="reset_doc"):
            st.session_state.doc_tor = None
            st.rerun()


def _handle_generate(uploaded_file, context: str):
    """Process uploaded file dan generate TOR."""
    with st.spinner("Membaca dokumen dan generating TOR..."):
        result = generate_from_document(
            uploaded_file.read(),
            uploaded_file.name,
            context,
        )

    if "error" in result:
        st.markdown(
            banner_html("error", result["error"], "error"),
            unsafe_allow_html=True,
        )
    else:
        st.session_state.doc_tor = result.get("tor_document", result)
        st.rerun()
```

### Step 2: Update `app.py`

```python
from components.form_document import render_document_tab

with tab_doc:
    render_document_tab()
```

### Step 3: Test

1. Upload file PDF → klik Generate → spinner → TOR preview
2. Upload file tanpa konteks → tetap generate
3. Tombol disabled saat belum ada file
4. "Generate Ulang" → reset state

## 6. Output yang Diharapkan

```
streamlit_app/components/
├── form_document.py    (~55 lines)
```

## 7. Dependencies

- **Task 01** — state
- **Task 03** — `mi()`, `banner_html()`
- **Task 04** — `generate_from_document()`
- **Task 06** — `render_tor_preview()`

## 8. Acceptance Criteria

- [ ] File uploader menerima PDF, TXT, MD, DOCX
- [ ] Konteks tambahan adalah opsional
- [ ] Generate button disabled saat belum ada file
- [ ] Spinner muncul saat generating
- [ ] Error ditampilkan via `.banner-error`
- [ ] TOR preview muncul setelah generate berhasil
- [ ] "Generate Ulang" button reset dan rerun

## 9. Estimasi

**Low** — Komponen paling sederhana dari semua 3 tab.
