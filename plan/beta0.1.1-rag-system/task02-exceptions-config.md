# Task 02 — Custom Exceptions & Config RAG System

## 1. Judul Task

Tambahkan custom exception untuk RAG System dan update `config.py` dengan parameter ChromaDB dan Embedder.

## 2. Deskripsi

RAG System membutuhkan exception khusus (`UnsupportedFormatError`, `VectorDBError`, `EmbeddingModelError`) dan parameter konfigurasi baru di `Settings` agar semua komponen bisa membaca config dari `.env` secara konsisten.

## 3. Tujuan Teknis

- Exception baru bisa di-raise dan di-catch dengan error code yang jelas
- `Settings` sudah punya semua field RAG (path ChromaDB, model embedding, dll)
- Mudah di-override via environment variable

## 4. Scope

### Yang dikerjakan
- Update `app/utils/errors.py` — tambah 3 exception baru
- Update `app/config.py` — tambah RAG config fields
- Update `.env.example` — tambah entry baru

### Yang tidak dikerjakan
- Implementasi class RAG (itu di task berikutnya)

## 5. Langkah Implementasi

### Step 1: Update `app/utils/errors.py`

Tambahkan di akhir file (setelah exception yang sudah ada):

```python
class UnsupportedFormatError(AppError):
    """File format tidak didukung untuk ingest."""
    code = "E009"
    message = "Format file tidak didukung."

    def __init__(self, filename: str, supported: set[str]):
        self.filename = filename
        self.supported = supported
        self.details = (
            f"Format file tidak didukung: {filename}. "
            f"Gunakan: {', '.join(sorted(supported))}"
        )
        super().__init__(self.details)


class VectorDBError(AppError):
    """ChromaDB tidak dapat diakses atau corrupt."""
    code = "E010"
    message = "Vector database tidak accessible."

    def __init__(self, details: str = ""):
        self.details = details
        super().__init__(details)


class EmbeddingModelError(AppError):
    """Model embedding Ollama belum di-pull atau gagal."""
    code = "E011"
    message = "Embedding model tidak tersedia."

    def __init__(self, model: str, details: str = ""):
        self.model = model
        self.details = (
            f"Embedding model '{model}' belum di-pull atau tidak tersedia. "
            f"Jalankan: ollama pull {model}"
        )
        super().__init__(self.details)
```

### Step 2: Update `app/config.py`

Tambahkan field-field berikut di dalam class `Settings`:

```python
# === RAG Settings ===
chroma_db_path: str = "./data/chroma_db"
chroma_collection_name: str = "tor_documents"
embedding_model: str = "bge-m3"
embedding_batch_size: int = 32
rag_documents_path: str = "./data/documents"
rag_top_k: int = 3
rag_score_threshold: float = 0.7
rag_chunk_size: int = 500
rag_chunk_overlap: int = 50
rag_min_chunk_size: int = 50
```

### Step 3: Update `.env.example`

Tambahkan di akhir file:
```env
# === RAG Settings ===
CHROMA_DB_PATH=./data/chroma_db
CHROMA_COLLECTION_NAME=tor_documents
EMBEDDING_MODEL=bge-m3
EMBEDDING_BATCH_SIZE=32
RAG_DOCUMENTS_PATH=./data/documents
RAG_TOP_K=3
RAG_SCORE_THRESHOLD=0.7
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_MIN_CHUNK_SIZE=50
```

### Step 4: Verifikasi

```python
from app.config import Settings
from app.utils.errors import UnsupportedFormatError, VectorDBError, EmbeddingModelError

settings = Settings()
assert settings.chroma_db_path == "./data/chroma_db"
assert settings.embedding_model == "bge-m3"
assert settings.rag_top_k == 3

# Test exceptions
try:
    raise UnsupportedFormatError("doc.pdf", {".md", ".txt"})
except UnsupportedFormatError as e:
    assert e.code == "E009"
    print(f"OK: {e.details}")

try:
    raise EmbeddingModelError("bge-m3")
except EmbeddingModelError as e:
    assert e.code == "E011"
    print(f"OK: {e.details}")

print("All config & exception checks passed!")
```

## 6. Output yang Diharapkan

```
OK: Format file tidak didukung: doc.pdf. Gunakan: .md, .txt
OK: Embedding model 'bge-m3' belum di-pull atau tidak tersedia. Jalankan: ollama pull bge-m3
All config & exception checks passed!
```

## 7. Dependencies

- **Task 01 (beta0.1.0)** — `app/utils/errors.py` dan `app/config.py` sudah ada

## 8. Acceptance Criteria

- [ ] `UnsupportedFormatError`, `VectorDBError`, `EmbeddingModelError` bisa di-import
- [ ] Setiap exception punya field `code`, `message`, `details`
- [ ] `Settings().chroma_db_path` return nilai default yang benar
- [ ] `Settings().embedding_model` return `"bge-m3"` secara default
- [ ] `.env.example` ter-update dengan semua entry RAG

## 9. Estimasi

**Low** — ~30 menit
