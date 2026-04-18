# Task 02 — Document Parser: TXT & MD

## 1. Judul Task

Buat `DocumentParser` class dengan support parsing TXT dan MD files.

## 2. Deskripsi

Implementasikan class `DocumentParser` di `app/core/document_parser.py`. Mulai dengan format paling sederhana — TXT dan MD — yang hanya butuh decode UTF-8.

## 3. Tujuan Teknis

- Class `DocumentParser` dengan method `parse(file_bytes, filename) -> str`
- Validasi file extension terhadap `SUPPORTED_FORMATS`
- Validasi ukuran file (max 20MB)
- Validasi output tidak kosong (min 50 chars)
- TXT/MD: decode UTF-8

## 4. Scope

### Yang dikerjakan
- `app/core/document_parser.py` — class + TXT/MD parsing
- Validasi: extension, size, content length
- Custom exception `DocumentParseError`

### Yang tidak dikerjakan
- PDF parsing (task selanjutnya)
- DOCX parsing (task selanjutnya)

## 5. Langkah Implementasi

### Step 1: Tambah exception di `app/utils/errors.py`

```python
class DocumentParseError(AppError):
    """Error saat parsing dokumen."""
    def __init__(self, message: str, details: str = None):
        super().__init__(
            code="DOCUMENT_PARSE_ERROR",
            message=message,
            details=details,
        )
```

### Step 2: Buat `app/core/document_parser.py`

```python
import logging
from pathlib import Path
from app.utils.errors import DocumentParseError

logger = logging.getLogger("ai-agent-hybrid.document_parser")


class DocumentParser:
    """Ekstrak teks dari berbagai format dokumen."""

    SUPPORTED_FORMATS = [".pdf", ".txt", ".md", ".docx"]
    MAX_FILE_SIZE_MB = 20
    MIN_TEXT_LENGTH = 50

    @staticmethod
    async def parse(file_bytes: bytes, filename: str) -> str:
        """Parse file bytes ke plain text."""
        ext = Path(filename).suffix.lower()

        # Validate extension
        if ext not in DocumentParser.SUPPORTED_FORMATS:
            raise DocumentParseError(
                message=f"Format '{ext}' tidak didukung.",
                details=f"Format yang didukung: {', '.join(DocumentParser.SUPPORTED_FORMATS)}",
            )

        # Validate size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > DocumentParser.MAX_FILE_SIZE_MB:
            raise DocumentParseError(
                message=f"File terlalu besar: {size_mb:.1f}MB (maks {DocumentParser.MAX_FILE_SIZE_MB}MB).",
            )

        # Parse based on extension
        if ext in (".txt", ".md"):
            text = DocumentParser._parse_text(file_bytes)
        elif ext == ".pdf":
            raise DocumentParseError(message="PDF parsing belum diimplementasi.")
        elif ext == ".docx":
            raise DocumentParseError(message="DOCX parsing belum diimplementasi.")

        # Validate content
        if len(text.strip()) < DocumentParser.MIN_TEXT_LENGTH:
            raise DocumentParseError(
                message="Dokumen terlalu pendek atau kosong.",
                details=f"Minimal {DocumentParser.MIN_TEXT_LENGTH} karakter.",
            )

        logger.info(f"Parsed '{filename}': {len(text)} chars")
        return text.strip()

    @staticmethod
    def _parse_text(file_bytes: bytes) -> str:
        """Parse TXT/MD file."""
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1")
            except Exception:
                raise DocumentParseError(message="Tidak bisa membaca encoding file.")
```

### Step 3: Test manual

```python
import asyncio
from app.core.document_parser import DocumentParser

text = asyncio.run(DocumentParser.parse(b"Ini dokumen test " * 10, "test.txt"))
print(len(text), "chars")
```

## 6. Output yang Diharapkan

```python
>>> text = await DocumentParser.parse(b"Dokumen panjang...", "laporan.txt")
>>> len(text) > 50
True

>>> await DocumentParser.parse(b"short", "file.txt")
# raises DocumentParseError: "Dokumen terlalu pendek"

>>> await DocumentParser.parse(b"data", "file.exe")
# raises DocumentParseError: "Format '.exe' tidak didukung"
```

## 7. Dependencies

- **Task 01** — dependencies installed

## 8. Acceptance Criteria

- [ ] `DocumentParser` class ada di `app/core/document_parser.py`
- [ ] TXT dan MD bisa di-parse
- [ ] Validasi: extension, size (max 20MB), content length (min 50 chars)
- [ ] Fallback encoding: UTF-8 → Latin-1
- [ ] `DocumentParseError` exception terdaftar
- [ ] Logging saat parse berhasil

## 9. Estimasi

**Low** — ~30 menit
