# Task 01: Export Service Layer

> **File Target**: `app/services/document_exporter.py`
> **Dependency**: Tidak ada (task pertama)
> **Status**: [ ] Belum Dikerjakan

## 1. Tujuan

Membuat service class `DocumentExporterService` yang bertanggung jawab mengkonversi string Markdown TOR menjadi file bytes dalam format `.docx`, `.pdf`, dan `.md`. Service ini akan menjadi satu-satunya titik konversi dokumen di seluruh sistem (menggantikan logika lokal di frontend).

## 2. Prerequisite — Verifikasi Dependensi

Dependensi berikut **sudah terdaftar** di `requirements.txt` (tidak perlu install baru):

| Package | Line | Kegunaan |
|---|---|---|
| `python-docx>=1.0` | L34 | Manipulasi file Microsoft Word |
| `markdown>=3.0` | L37 | Konversi MD → HTML |
| `xhtml2pdf>=0.2.11` | L38 | Konversi HTML → PDF |

- [ ] Verifikasi ketiga package di atas ada di `requirements.txt`.

## 3. Buat Error Class

Tambahkan error baru di `app/utils/errors.py` agar konsisten dengan pola error handling proyek (`AppError` base class):

- [ ] Tambahkan class `ExportError` di `app/utils/errors.py`:

```python
class ExportError(AppError):
    """E013 — Error saat mengekspor dokumen."""
    def __init__(self, message: str, details: str | None = None):
        super().__init__(
            message=message,
            code="E013",
            details=details,
        )
```

## 4. Buat File Service

- [ ] Buat file `app/services/document_exporter.py`.

### 4.1 Class Skeleton

```python
import io
import re
import logging

import markdown
from xhtml2pdf import pisa
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.utils.errors import ExportError

logger = logging.getLogger("ai-agent-hybrid.export")

SUPPORTED_FORMATS = {"docx", "pdf", "md"}


class DocumentExporterService:
    """Konversi Markdown TOR ke berbagai format dokumen."""

    def export(self, md_text: str, fmt: str) -> bytes:
        """Dispatcher utama. Routing ke method spesifik berdasarkan format.

        Args:
            md_text: String konten TOR dalam format Markdown.
            fmt: Format target — "docx", "pdf", atau "md".

        Returns:
            bytes: File content sebagai binary.

        Raises:
            ExportError: Jika format tidak didukung atau konversi gagal.
        """
        ...

    def export_to_md(self, md_text: str) -> bytes:
        ...

    def export_to_pdf(self, md_text: str) -> bytes:
        ...

    def export_to_docx(self, md_text: str) -> bytes:
        ...
```

### 4.2 Implementasi `export()` — Dispatcher

- [ ] Implementasikan method `export()`:

```python
def export(self, md_text: str, fmt: str) -> bytes:
    fmt = fmt.lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            message=f"Format '{fmt}' tidak didukung.",
            details=f"Format yang didukung: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )
    method_map = {
        "md": self.export_to_md,
        "pdf": self.export_to_pdf,
        "docx": self.export_to_docx,
    }
    try:
        result = method_map[fmt](md_text)
        logger.info(f"Export sukses: format={fmt}, size={len(result)} bytes")
        return result
    except ExportError:
        raise
    except Exception as e:
        logger.error(f"Export gagal: format={fmt}, error={e}")
        raise ExportError(
            message=f"Gagal mengekspor ke format {fmt}.",
            details=str(e),
        )
```

### 4.3 Implementasi `export_to_md()`

- [ ] Implementasikan method `export_to_md()`:

```python
def export_to_md(self, md_text: str) -> bytes:
    """Return raw Markdown text sebagai UTF-8 bytes. Tanpa konversi."""
    return md_text.encode("utf-8")
```

### 4.4 Implementasi `export_to_pdf()`

Logika ini **dimigrasikan** dari `streamlit_app/utils/formatters.py:export_to_pdf()` dengan styling yang sama.

- [ ] Implementasikan method `export_to_pdf()`:

```python
def export_to_pdf(self, md_text: str) -> bytes:
    """Konversi Markdown → HTML → PDF via xhtml2pdf."""
    html_body = markdown.markdown(
        md_text, extensions=["tables", "fenced_code"]
    )
    styled_html = f"""<html><head><style>
        body {{ font-family: 'Helvetica', Arial, sans-serif;
               font-size: 12pt; line-height: 1.6; color: #222; 
               margin: 40px; }}
        h1 {{ font-size: 18pt; text-align: center; margin-bottom: 20px; }}
        h2 {{ font-size: 14pt; border-bottom: 1px solid #ccc;
              padding-bottom: 5px; margin-top: 25px; }}
        h3 {{ font-size: 12pt; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f4f4f4; font-weight: bold; }}
        ul, ol {{ margin-left: 20px; }}
    </style></head><body>{html_body}</body></html>"""

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(styled_html), dest=buffer)
    if pisa_status.err:
        raise ExportError(
            message="Gagal membuat PDF.",
            details=f"xhtml2pdf error count: {pisa_status.err}",
        )
    return buffer.getvalue()
```

### 4.5 Implementasi `export_to_docx()` — Paling Kompleks

Konversi Markdown ke python-docx elements menggunakan regex parsing sederhana. Ini **bukan** full Markdown parser — cukup menangani elemen yang lazim muncul di output TOR Gemini.

- [ ] Implementasikan method `export_to_docx()`:

```python
def export_to_docx(self, md_text: str) -> bytes:
    """Konversi Markdown → python-docx Document."""
    doc = Document()

    # --- Page style ---
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)

    lines = md_text.split("\n")
    i = 0
    table_buffer: list[str] = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # --- Flush table jika baris bukan tabel ---
        if table_buffer and not stripped.startswith("|"):
            self._flush_table(doc, table_buffer)
            table_buffer = []

        # --- Heading ---
        heading_match = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            doc.add_heading(text, level=min(level, 4))
            i += 1
            continue

        # --- Table row ---
        if stripped.startswith("|") and stripped.endswith("|"):
            # Skip separator rows (|---|---|)
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                i += 1
                continue
            table_buffer.append(stripped)
            i += 1
            continue

        # --- Unordered list ---
        list_match = re.match(r"^[-*]\s+(.+)$", stripped)
        if list_match:
            text = list_match.group(1)
            p = doc.add_paragraph(style="List Bullet")
            self._apply_inline_formatting(p, text)
            i += 1
            continue

        # --- Ordered list ---
        olist_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if olist_match:
            text = olist_match.group(1)
            p = doc.add_paragraph(style="List Number")
            self._apply_inline_formatting(p, text)
            i += 1
            continue

        # --- Horizontal rule ---
        if re.match(r"^-{3,}$|^\*{3,}$|^_{3,}$", stripped):
            doc.add_paragraph("_" * 50)
            i += 1
            continue

        # --- Empty line (skip) ---
        if not stripped:
            i += 1
            continue

        # --- Regular paragraph ---
        p = doc.add_paragraph()
        self._apply_inline_formatting(p, stripped)
        i += 1

    # Flush remaining table
    if table_buffer:
        self._flush_table(doc, table_buffer)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
```

- [ ] Implementasikan helper `_flush_table()`:

```python
def _flush_table(self, doc: Document, rows: list[str]) -> None:
    """Parse baris-baris tabel Markdown menjadi tabel Word."""
    parsed = []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        parsed.append(cells)

    if not parsed:
        return

    n_cols = max(len(r) for r in parsed)
    table = doc.add_table(rows=len(parsed), cols=n_cols)
    table.style = "Table Grid"

    for r_idx, row_data in enumerate(parsed):
        for c_idx, cell_text in enumerate(row_data):
            if c_idx < n_cols:
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_text
                # Bold header row
                if r_idx == 0:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.bold = True
```

- [ ] Implementasikan helper `_apply_inline_formatting()`:

```python
def _apply_inline_formatting(self, paragraph, text: str) -> None:
    """Parse inline Markdown (bold, italic) dan terapkan ke paragraph runs."""
    # Pattern: **bold**, *italic*, ***bold-italic***
    parts = re.split(r"(\*{1,3}[^*]+\*{1,3})", text)
    for part in parts:
        if not part:
            continue
        bold_match = re.match(r"^\*\*([^*]+)\*\*$", part)
        italic_match = re.match(r"^\*([^*]+)\*$", part)
        if bold_match:
            run = paragraph.add_run(bold_match.group(1))
            run.bold = True
        elif italic_match:
            run = paragraph.add_run(italic_match.group(1))
            run.italic = True
        else:
            paragraph.add_run(part)
```

## 5. Registrasi Service

### 5.1 Expose di `app/main.py` (lifespan)

- [ ] Tambahkan inisialisasi `DocumentExporterService` di fungsi `lifespan()` dalam `app/main.py`:

```python
# Tambahkan setelah block inisialisasi GenerateService (sekitar line 79)
from app.services.document_exporter import DocumentExporterService
app.state.document_exporter = DocumentExporterService()
logger.info("Document Exporter Service initialized")
```

### 5.2 Expose `TORCache` ke `app.state`

Saat ini variable `tor_cache` di `main.py` line 57 hanya di-inject ke `GenerateService` tetapi **tidak tersedia langsung di `app.state`**. Task 02 (Export API) membutuhkan akses langsung.

- [ ] Tambahkan di `app/main.py` (setelah line 57, di bawah `tor_cache = TORCache(...)`):

```python
app.state.tor_cache = tor_cache  # expose untuk route export
```

## 6. Acceptance Criteria

- [ ] File `app/services/document_exporter.py` ada dan tidak ada error saat `import`.
- [ ] `DocumentExporterService().export("# Test", "md")` → return `b"# Test"`.
- [ ] `DocumentExporterService().export("# Test", "pdf")` → return bytes yang dimulai `b"%PDF"`.
- [ ] `DocumentExporterService().export("# Test", "docx")` → return bytes yang bisa di-load oleh `Document(io.BytesIO(result))`.
- [ ] `DocumentExporterService().export("# Test", "xlsx")` → raise `ExportError`.
- [ ] `python -c "from app.services.document_exporter import DocumentExporterService"` berhasil tanpa error.
