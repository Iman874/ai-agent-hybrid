# Task 01 — Pydantic Data Models untuk RAG System

## 1. Judul Task

Implementasi model Pydantic untuk seluruh data structure RAG System.

## 2. Deskripsi

Membuat semua Pydantic schema yang digunakan di seluruh RAG pipeline: `Document`, `DocumentMetadata`, `Chunk`, `ChunkMetadata`, `RetrievedChunk`, `IngestResult`, dan `RAGStatus`. File ini menjadi fondasi type-safe untuk semua komponen.

## 3. Tujuan Teknis

- Semua class dapat di-import dari `app/models/rag.py`
- Field memiliki type annotation yang benar
- `IngestResult` dan `RAGStatus` bisa langsung dipakai sebagai response model FastAPI

## 4. Scope

### Yang dikerjakan
- `app/models/rag.py` — semua Pydantic models

### Yang tidak dikerjakan
- Logic (parsing, embedding, dll)
- Database integration

## 5. Langkah Implementasi

### Step 1: Buat `app/models/rag.py`

```python
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


VALID_CATEGORIES = Literal["tor_template", "tor_example", "guideline"]


class DocumentMetadata(BaseModel):
    source: str                      # filename
    category: str                    # "tor_template" | "tor_example" | "guideline"
    file_type: str                   # "md" | "txt"
    char_count: int
    loaded_at: datetime


class Document(BaseModel):
    id: str                          # hash-based ID
    content: str                     # raw text content
    metadata: DocumentMetadata


class ChunkMetadata(BaseModel):
    source: str
    category: str
    file_type: str
    chunk_index: int                 # 0-based
    total_chunks: int
    char_count: int
    loaded_at: datetime


class Chunk(BaseModel):
    id: str                          # "{doc_id}_chunk_{index}"
    text: str
    metadata: ChunkMetadata


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float                     # similarity score (0.0 - 1.0)
    metadata: ChunkMetadata


class IngestFileDetail(BaseModel):
    filename: str
    chunks: int
    char_count: int
    status: str                      # "ingested" | "skipped" | "error"


class IngestResult(BaseModel):
    status: str                      # "success" | "partial"
    ingested_files: int
    total_chunks: int
    collection_size: int
    details: list[IngestFileDetail]


class VectorDBInfo(BaseModel):
    type: str = "chromadb"
    collection: str
    total_documents: int
    total_chunks: int
    embedding_model: str
    embedding_dimensions: int = 1024


class RAGDocumentInfo(BaseModel):
    filename: str
    category: str
    chunks: int
    ingested_at: str


class RAGStatus(BaseModel):
    status: str                      # "healthy" | "degraded"
    vector_db: VectorDBInfo
    documents: list[RAGDocumentInfo]
```

### Step 2: Update `app/models/__init__.py`

Tambahkan baris berikut di akhir file:
```python
# RAG Models
from app.models.rag import (
    Document,
    DocumentMetadata,
    Chunk,
    ChunkMetadata,
    RetrievedChunk,
    IngestResult,
    IngestFileDetail,
    RAGStatus,
    VectorDBInfo,
    RAGDocumentInfo,
    VALID_CATEGORIES,
)
```

### Step 3: Verifikasi

```python
from app.models.rag import (
    Document, DocumentMetadata, Chunk, ChunkMetadata,
    RetrievedChunk, IngestResult, IngestFileDetail, RAGStatus
)
from datetime import datetime

# Test Document
meta = DocumentMetadata(
    source="test.md", category="tor_example",
    file_type="md", char_count=500, loaded_at=datetime.utcnow()
)
doc = Document(id="abc123", content="Isi dokumen", metadata=meta)
assert doc.id == "abc123"

# Test Chunk
chunk_meta = ChunkMetadata(
    source="test.md", category="tor_example", file_type="md",
    chunk_index=0, total_chunks=3, char_count=200, loaded_at=datetime.utcnow()
)
chunk = Chunk(id="abc123_chunk_0", text="Potongan teks", metadata=chunk_meta)
assert "chunk_0" in chunk.id

# Test RetrievedChunk
rc = RetrievedChunk(id="abc123_chunk_0", text="Teks", score=0.87, metadata=chunk_meta)
assert 0.0 <= rc.score <= 1.0

# Test IngestResult
result = IngestResult(
    status="success",
    ingested_files=2,
    total_chunks=35,
    collection_size=89,
    details=[
        IngestFileDetail(filename="test.md", chunks=18, char_count=4000, status="ingested")
    ]
)
assert result.ingested_files == 2

print("All RAG model tests passed!")
```

## 6. Output yang Diharapkan

```
All RAG model tests passed!
```

## 7. Dependencies

- **Task 01 (beta0.1.0)** — struktur project dan venv sudah ada

## 8. Acceptance Criteria

- [ ] `Document`, `DocumentMetadata`, `Chunk`, `ChunkMetadata` ter-import tanpa error
- [ ] `RetrievedChunk.score` bertype `float`
- [ ] `IngestResult` bisa diinstansiasi dengan semua field benar
- [ ] `RAGStatus` ter-serialisasi ke JSON tanpa error
- [ ] Semua class ter-export dari `app/models/__init__.py`

## 9. Estimasi

**Low** — ~30 menit
