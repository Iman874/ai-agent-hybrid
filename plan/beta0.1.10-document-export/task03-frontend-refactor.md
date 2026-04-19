# Task 03: Frontend Refactor & Streamlit Integration

> **File Target**: `streamlit_app/api/client.py`, `streamlit_app/components/tor_preview.py`, `streamlit_app/utils/formatters.py`
> **Dependency**: ⚠️ Membutuhkan Task 01 + Task 02 selesai (endpoint harus sudah aktif)
> **Status**: [ ] Belum Dikerjakan

## 1. Tujuan

Refactoring komponen Streamlit agar semua operasi export dokumen dilakukan melalui Backend API (endpoint dari Task 02), menghapus ketergantungan langsung pada library `xhtml2pdf` di sisi frontend, dan menambahkan tombol download `.docx` yang sebelumnya belum ada.

## 2. Tambah Fungsi di API Client

File target: `streamlit_app/api/client.py` (file sudah ada, 245 baris — **jangan buat file baru**).

- [ ] Tambahkan fungsi `export_document()` di akhir file `streamlit_app/api/client.py` (sebelum baris terakhir):

```python
def export_document(session_id: str, fmt: str = "docx") -> bytes | None:
    """Download file TOR hasil export dari backend.

    Args:
        session_id: ID session yang TOR-nya sudah di-generate.
        fmt: Format file — "docx", "pdf", atau "md".

    Returns:
        bytes: File content binary, atau None jika gagal.
    """
    try:
        resp = requests.get(
            f"{API_URL}/export/{session_id}",
            params={"format": fmt},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content
    except requests.ConnectionError:
        st.error("Backend tidak bisa dihubungi untuk export.")
        return None
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            st.error("TOR belum di-generate untuk session ini.")
        else:
            st.error(f"Export gagal: HTTP {e.response.status_code}")
        return None
    except Exception as e:
        st.error(f"Export error: {e}")
        return None
```

## 3. Refactor `tor_preview.py`

File target: `streamlit_app/components/tor_preview.py` (80 baris saat ini).

Perubahan yang harus dilakukan:

### 3.1 Hapus Import Lama, Tambah Import Baru

- [ ] Ubah import di bagian atas file:

```diff
 # streamlit_app/components/tor_preview.py
 """Reusable TOR document preview component."""
 
 import streamlit as st
 from utils.icons import mi, mi_inline, banner_html
-from utils.formatters import export_to_pdf
+from api.client import export_document
```

### 3.2 Tambah Parameter `session_id` di Signature

- [ ] Ubah signature fungsi `render_tor_preview()`:

```diff
 def render_tor_preview(
     tor: dict,
+    session_id: str,
     escalation_info: dict | None = None,
     key_suffix: str = "",
 ):
     """Render TOR preview lengkap: banner, metadata, content, downloads.
 
     Args:
         tor: TOR document dict {"content": "...", "metadata": {...}}
+        session_id: ID session untuk fetch export dari backend
         escalation_info: Optional escalation data
         key_suffix: Unique key suffix untuk download buttons
     """
```

### 3.3 Ubah Section Download — Dari 2 Kolom ke 3 Kolom

- [ ] Replace seluruh blok download buttons (line 44-66 di versi lama):

**SEBELUM** (kode lama):
```python
    # --- Download Buttons ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇ Download .md",
            tor["content"],
            f"tor{key_suffix}.md",
            "text/markdown",
            use_container_width=True,
            key=f"dl_md{key_suffix}",
        )
    with c2:
        pdf = export_to_pdf(tor["content"])
        st.download_button(
            "⬇ Download .pdf",
            pdf,
            f"tor{key_suffix}.pdf",
            "application/pdf",
            use_container_width=True,
            key=f"dl_pdf{key_suffix}",
            disabled=not pdf,
        )
```

**SESUDAH** (kode baru):
```python
    # --- Download Buttons (via Backend API) ---
    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        docx_bytes = export_document(session_id, "docx")
        st.download_button(
            "📄 Download .docx",
            data=docx_bytes or b"",
            file_name=f"tor{key_suffix}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key=f"dl_docx{key_suffix}",
            disabled=not docx_bytes,
        )

    with c2:
        pdf_bytes = export_document(session_id, "pdf")
        st.download_button(
            "📕 Download .pdf",
            data=pdf_bytes or b"",
            file_name=f"tor{key_suffix}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_pdf{key_suffix}",
            disabled=not pdf_bytes,
        )

    with c3:
        md_bytes = export_document(session_id, "md")
        st.download_button(
            "📝 Download .md",
            data=md_bytes or b"",
            file_name=f"tor{key_suffix}.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"dl_md{key_suffix}",
            disabled=not md_bytes,
        )
```

> **Catatan Performance**: Implementasi di atas memanggil API 3x saat render. Jika ini menjadi lambat, bisa di-optimize nanti dengan caching `@st.cache_data(ttl=60)` atau lazy-load saat button diklik. Untuk MVP saat ini, 3 calls sudah cukup.

## 4. Update Semua Pemanggil `render_tor_preview()`

Karena signature berubah (tambah `session_id`), semua tempat yang memanggil fungsi ini harus diupdate.

- [ ] Cari semua penggunaan `render_tor_preview(` di codebase Streamlit:

```bash
grep -rn "render_tor_preview(" streamlit_app/
```

- [ ] Untuk setiap pemanggil, tambahkan `session_id=st.session_state.session_id`:

```diff
 render_tor_preview(
     tor=st.session_state.tor_document,
+    session_id=st.session_state.session_id,
     escalation_info=st.session_state.get("escalation_info"),
 )
```

## 5. Deprecate Legacy `formatters.py`

File target: `streamlit_app/utils/formatters.py`.

**Jangan hapus file** — bisa ada modul lain yang mengimport. Cukup deprecate.

- [ ] Replace isi `streamlit_app/utils/formatters.py`:

```python
# streamlit_app/utils/formatters.py
"""Text and document formatting utilities.

DEPRECATED (beta 0.1.10): Export functions have been centralized to
the backend service at app/services/document_exporter.py.
Use the API endpoint GET /api/v1/export/{session_id} instead.
"""

import warnings
import io
import markdown
from xhtml2pdf import pisa


def export_to_pdf(md_text: str) -> bytes:
    """Convert markdown text ke PDF bytes.

    DEPRECATED: Gunakan backend API endpoint /api/v1/export/{session_id}?format=pdf

    Args:
        md_text: Markdown source text

    Returns:
        bytes: PDF binary data (kosong jika error)
    """
    warnings.warn(
        "export_to_pdf() is deprecated. Use backend API /api/v1/export/ instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    styled = f"""<html><head><style>
        body {{ font-family: 'Inter', Helvetica, Arial, sans-serif;
               font-size: 12pt; line-height: 1.5; color: #222; }}
        h1 {{ font-size: 18pt; text-align: center; margin-bottom: 20px; }}
        h2 {{ font-size: 14pt; border-bottom: 1px solid #ccc;
              padding-bottom: 5px; margin-top: 25px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f4f4f4; }}
    </style></head><body>{html}</body></html>"""
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled), dest=result)
    return b"" if pisa_status.err else result.getvalue()
```

## 6. Acceptance Criteria

- [ ] `streamlit_app/components/tor_preview.py` tidak lagi mengimport `export_to_pdf`.
- [ ] `from api.client import export_document` berhasil dan fungsi callable.
- [ ] Tombol download muncul **3 buah**: `.docx`, `.pdf`, `.md` (bukan 2 seperti sebelumnya).
- [ ] Klik tombol Download `.docx` → file ter-download dan bisa dibuka di Microsoft Word.
- [ ] Klik tombol Download `.pdf` → file ter-download dan bisa dibuka di PDF viewer.
- [ ] Klik tombol Download `.md` → file ter-download dan isinya identik dengan konten preview.
- [ ] `grep -rn "from utils.formatters import export_to_pdf" streamlit_app/` → **0 hasil** (tidak ada lagi import langsung).
- [ ] Calling legacy `export_to_pdf()` menghasilkan `DeprecationWarning`.
