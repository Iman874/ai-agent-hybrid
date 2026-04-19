# Task 06: Component — TOR Preview (`components/tor_preview.py`)

## Status: 🔲 Pending

---

## 1. Judul Task

Membuat komponen reusable TOR Preview dengan Material Icons dan banner styles.

## 2. Deskripsi

Extract `render_tor_preview()` dari monolit dan upgrade dengan Material Icons,
banner styling, dan PDF export. Komponen ini dipakai oleh 3 tab (Chat, Direct,
Document), sehingga harus siap lebih dulu.

## 3. Tujuan Teknis

- `render_tor_preview(tor, escalation_info, key_suffix)` — single reusable function
- Success banner menggunakan `.banner-success` CSS class + Material Icon `task_alt`
- Download buttons menggunakan Material Icons (`download`, `picture_as_pdf`)
- Escalation warning menggunakan `.banner-warning` + Material Icon `warning`

## 4. Scope

**Yang dikerjakan:**
- `components/tor_preview.py` — fungsi `render_tor_preview()`
- `utils/formatters.py` — fungsi `export_to_pdf()` (extract dari monolit)

**Yang TIDAK dikerjakan:**
- Tab UI (Task 09-11)
- Sidebar (Task 07)

## 5. Langkah Implementasi

### Step 1: Buat `utils/formatters.py`

Extract dari `streamlit_app.py` lines 209-221:

```python
# streamlit_app/utils/formatters.py
"""Text and document formatting utilities."""

import io
import markdown
from xhtml2pdf import pisa


def export_to_pdf(md_text: str) -> bytes:
    """Convert markdown text ke PDF bytes.

    Args:
        md_text: Markdown source text

    Returns:
        bytes: PDF binary data (kosong jika error)
    """
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

### Step 2: Buat `components/tor_preview.py`

```python
# streamlit_app/components/tor_preview.py
"""Reusable TOR document preview component."""

import streamlit as st
from utils.icons import mi, mi_inline, banner_html
from utils.formatters import export_to_pdf


def render_tor_preview(
    tor: dict,
    escalation_info: dict | None = None,
    key_suffix: str = "",
):
    """Render TOR preview lengkap: banner, metadata, content, downloads.

    Args:
        tor: TOR document dict {"content": "...", "metadata": {...}}
        escalation_info: Optional escalation data
        key_suffix: Unique key suffix untuk download buttons
    """
    st.divider()

    # --- Success banner ---
    st.markdown(
        banner_html("task_alt", "TOR Berhasil Dibuat!", "success"),
        unsafe_allow_html=True,
    )

    # --- Metadata (collapsible) ---
    with st.expander(
        mi_inline("info", "Metadata", 18) if False else "Metadata",
        expanded=False,
    ):
        meta = tor.get("metadata", {})
        c = st.columns(4)
        c[0].metric("Model", meta.get("generated_by", "—"))
        c[1].metric("Mode", meta.get("mode", "—"))
        c[2].metric("Kata", meta.get("word_count", 0))
        c[3].metric("Waktu", f'{meta.get("generation_time_ms", 0)}ms')

    # --- TOR Content ---
    st.markdown(tor["content"])

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

    # --- Escalation Warning ---
    if escalation_info:
        reason = escalation_info.get("reason", "")
        trigger = escalation_info.get("triggered_by", "")
        st.markdown(
            banner_html(
                "warning",
                f"TOR via eskalasi · <strong>{trigger}</strong> · {reason}",
                "warning",
            ),
            unsafe_allow_html=True,
        )
```

### Step 3: Test dengan dummy data

```python
# Di app.py sementara:
from components.tor_preview import render_tor_preview

dummy_tor = {
    "content": "# TOR\n## Workshop AI\nIni konten TOR test.",
    "metadata": {
        "generated_by": "gemini-2.0-flash",
        "mode": "standard",
        "word_count": 850,
        "generation_time_ms": 3200,
    },
}
render_tor_preview(dummy_tor, key_suffix="_test")
```

## 6. Output yang Diharapkan

```
streamlit_app/
├── components/
│   └── tor_preview.py    (~70 lines)
├── utils/
│   └── formatters.py     (~30 lines)
```

## 7. Dependencies

- **Task 01** — folder structure
- **Task 02** — CSS banner classes
- **Task 03** — `mi()`, `mi_inline()`, `banner_html()`

## 8. Acceptance Criteria

- [ ] `render_tor_preview()` menampilkan success banner hijau dengan icon `task_alt`
- [ ] Metadata expander berfungsi (Model, Mode, Kata, Waktu)
- [ ] TOR content di-render sebagai markdown
- [ ] Download .md dan .pdf buttons berfungsi
- [ ] Escalation warning muncul jika `escalation_info` diberikan
- [ ] `export_to_pdf()` menghasilkan valid PDF bytes
- [ ] Komponen bisa dipanggil dari tab manapun dengan `key_suffix` berbeda

## 9. Estimasi

**Medium** — Extract + upgrade styling + test PDF export.
