# Task 03 — Document Loader

## 1. Judul Task

Implementasi `DocumentLoader` — baca file `.md` dan `.txt` dari filesystem atau upload bytes.

## 2. Deskripsi

Membuat class `DocumentLoader` yang bertanggung jawab untuk membaca file dokumen dari directory atau dari bytes hasil upload API. Class ini menghasilkan objek `Document` ber-metadata lengkap yang siap di-split.

## 3. Tujuan Teknis

- `load_from_directory(dir_path, category)` — scan folder dan baca semua `.md` / `.txt`
- `load_from_upload(filename, content, category)` — baca dari bytes upload
- Document ID di-generate dengan `sha256(filename + content[:100])[:16]`
- Raise `UnsupportedFormatError` jika format tidak `.md` / `.txt`

## 4. Scope

### Yang dikerjakan
- `app/rag/document_loader.py` — class `DocumentLoader`
- `app/rag/__init__.py` — init module

### Yang tidak dikerjakan
- Text splitting (itu task 04)
- Embedding (itu task 05)

## 5. Langkah Implementasi

### Step 1: Buat `app/rag/__init__.py`

```python
"""RAG Pipeline Module"""
```

### Step 2: Buat `app/rag/document_loader.py`

```python
import hashlib
import logging
from datetime import datetime
from pathlib import Path

from app.models.rag import Document, DocumentMetadata
from app.utils.errors import UnsupportedFormatError

logger = logging.getLogger("ai-agent-hybrid.rag.loader")


class DocumentLoader:
    """Load dokumen dari filesystem atau uploaded bytes."""

    SUPPORTED_EXTENSIONS = {".md", ".txt"}

    def load_from_directory(self, dir_path: str, category: str) -> list[Document]:
        """Load semua file yang didukung dari directory (recursive)."""
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory tidak ditemukan: {dir_path}")

        documents = []
        for file_path in sorted(path.rglob("*")):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    doc = self._load_file(file_path, category)
                    documents.append(doc)
                    logger.debug(f"Loaded: {file_path.name} ({doc.metadata.char_count} chars)")
                except Exception as e:
                    logger.warning(f"Gagal load file {file_path.name}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {dir_path}")
        return documents

    def load_from_upload(self, filename: str, content: bytes, category: str) -> Document:
        """Load dari bytes hasil upload API."""
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported format: {filename}")
            raise UnsupportedFormatError(filename, self.SUPPORTED_EXTENSIONS)

        text = content.decode("utf-8")
        doc = self._create_document(filename, text, ext, category)
        logger.debug(f"Loaded from upload: {filename} ({doc.metadata.char_count} chars)")
        return doc

    def _load_file(self, path: Path, category: str) -> Document:
        text = path.read_text(encoding="utf-8")
        return self._create_document(path.name, text, path.suffix.lower(), category)

    def _load_file_by_path(self, file_path: str, category: str) -> Document:
        """Load dari absolute/relative path string."""
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFormatError(path.name, self.SUPPORTED_EXTENSIONS)
        return self._load_file(path, category)

    def _create_document(
        self, filename: str, text: str, ext: str, category: str
    ) -> Document:
        doc_id = hashlib.sha256(
            f"{filename}:{text[:100]}".encode()
        ).hexdigest()[:16]

        return Document(
            id=doc_id,
            content=text,
            metadata=DocumentMetadata(
                source=filename,
                category=category,
                file_type=ext.lstrip("."),
                char_count=len(text),
                loaded_at=datetime.utcnow(),
            ),
        )
```

### Step 3: Buat folder contoh dokumen

```bash
mkdir -p data/documents/templates
mkdir -p data/documents/examples
mkdir -p data/documents/guidelines
```

Buat file contoh `data/documents/examples/contoh_tor.md`:
```markdown
# TOR Workshop Penerapan AI

## Latar Belakang
Workshop ini diselenggarakan untuk meningkatkan kompetensi ASN.

## Tujuan
Peserta mampu memahami dasar-dasar pemanfaatan AI generatif.

## Ruang Lingkup
Pelatihan 3 hari untuk 30 peserta di Jakarta.

## Output
Sertifikat dan modul pelatihan digital.

## Timeline
Bulan Juli 2026, selama 3 hari kerja.
```

### Step 4: Verifikasi

```python
from app.rag.document_loader import DocumentLoader
from app.utils.errors import UnsupportedFormatError

loader = DocumentLoader()

# Test load dari directory
docs = loader.load_from_directory("./data/documents", "tor_example")
assert len(docs) >= 1
doc = docs[0]
assert doc.id is not None and len(doc.id) == 16
assert doc.metadata.file_type in ("md", "txt")
print(f"Test 1 passed: loaded {len(docs)} docs")

# Test load dari upload bytes
content = b"# Test TOR\n## Latar Belakang\nIni adalah contoh TOR sederhana."
doc2 = loader.load_from_upload("test.md", content, "tor_example")
assert doc2.metadata.source == "test.md"
assert doc2.metadata.category == "tor_example"
print("Test 2 passed: upload bytes OK")

# Test format tidak didukung
try:
    loader.load_from_upload("proposal.pdf", b"pdf content", "tor_example")
    assert False, "Harus raise UnsupportedFormatError"
except UnsupportedFormatError as e:
    assert e.code == "E009"
    print(f"Test 3 passed: {e.details}")

print("ALL DOCUMENT LOADER TESTS PASSED")
```

## 6. Output yang Diharapkan

```
Test 1 passed: loaded 1 docs
Test 2 passed: upload bytes OK
Test 3 passed: Format file tidak didukung: proposal.pdf. Gunakan: .md, .txt
ALL DOCUMENT LOADER TESTS PASSED
```

## 7. Dependencies

- **Task 01** — `Document`, `DocumentMetadata` models
- **Task 02** — `UnsupportedFormatError` exception

## 8. Acceptance Criteria

- [ ] `load_from_directory("./data/documents", "tor_example")` return list `Document` tidak kosong
- [ ] `Document.id` berupa 16-char hex string
- [ ] `Document.metadata.category` sesuai parameter
- [ ] `Document.metadata.char_count` sama dengan `len(doc.content)`
- [ ] `load_from_upload("test.pdf", ...)` raise `UnsupportedFormatError`
- [ ] File `.txt` dan `.md` keduanya bisa di-load

## 9. Estimasi

**Low** — ~1 jam
