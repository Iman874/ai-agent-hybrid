# Beta 0.1.1 — RAG System (Retrieval-Augmented Generation)

> **Modul**: RAG Pipeline
> **Versi**: beta0.1.1
> **Status**: Ready to Implement
> **Estimasi**: 3 hari kerja
> **Prasyarat**: beta0.1.0 (Chat Engine) sudah berjalan, Ollama + `bge-m3` model ter-pull

---

## 1. Overview

RAG System adalah **memori** sistem — berperan sebagai "senior project manager" yang membisikkan contoh dan referensi TOR kepada local LLM. Modul ini:

1. **Meng-ingest dokumen** referensi (contoh TOR, template, panduan) ke dalam vector database
2. **Memecah dokumen** menjadi chunks yang optimal untuk retrieval
3. **Menghasilkan embedding** untuk setiap chunk menggunakan model lokal (`bge-m3` via Ollama)
4. **Menyimpan** embedding + metadata ke ChromaDB (persistent di disk)
5. **Meretrieve** chunks yang paling relevan berdasarkan similarity search terhadap query user
6. **Memformat** hasil retrieval menjadi context string yang siap di-inject ke prompt LLM

Tanpa modul ini, Chat Engine (beta0.1.0) tetap bisa jalan — hanya saja tanpa konteks referensi sehingga hasilnya kurang tajam.

---

## 2. Scope

### ✅ Yang dikerjakan di modul ini

| Item | Detail |
|---|---|
| Document Loader | Baca file `.md`, `.txt` dari folder `data/documents/` |
| Text Splitter | Chunking dengan separators hierarkis, overlap, metadata |
| Embedding Generator | Panggil `bge-m3` via Ollama untuk generate embedding vektor |
| Vector Store | Wrapper ChromaDB: upsert, query, delete, collection info |
| Retriever | Similarity search + score threshold filtering |
| Context Formatter | Format chunks jadi teks untuk di-inject ke prompt |
| Ingest Endpoint | `POST /api/v1/rag/ingest` — upload & index dokumen |
| Ingest Script | CLI script `scripts/ingest_documents.py` untuk batch ingest |
| RAG Info Endpoint | `GET /api/v1/rag/status` — cek status vector DB |

### ❌ Yang TIDAK dikerjakan di modul ini

| Item | Alasan |
|---|---|
| PDF parsing | Ditunda ke versi mendatang. Awalnya fokus `.md` dan `.txt` saja |
| Semantic re-ranking | Over-engineering untuk v0.1. Simple similarity search cukup |
| Multi-collection | Satu collection `tor_documents` cukup untuk saat ini |
| Auto-embedding model download | User harus manual `ollama pull bge-m3` |

---

## 3. Input / Output

### Input: Ingestion (dokumen → vector DB)

```
File System Input:
    data/documents/
    ├── templates/
    │   └── template_workshop.md
    ├── examples/
    │   └── tor_workshop_ai_2025.md
    └── guidelines/
        └── guideline_bahasa_formal.md

API Input (POST /api/v1/rag/ingest):
    multipart/form-data
    - files: [UploadFile, UploadFile, ...]
    - category: "tor_template" | "tor_example" | "guideline"
```

### Output: Ingestion

```json
{
    "status": "success",
    "ingested_files": 3,
    "total_chunks": 42,
    "collection_size": 156,
    "details": [
        {"filename": "template_workshop.md", "chunks": 12, "status": "ok"},
        {"filename": "tor_workshop_ai_2025.md", "chunks": 18, "status": "ok"},
        {"filename": "guideline_bahasa_formal.md", "chunks": 12, "status": "ok"}
    ]
}
```

### Input: Retrieval (query dari ChatService)

```python
class RetrievalQuery:
    query: str                          # teks dari user message / judul TOR
    top_k: int = 3                      # jumlah chunks yang diambil
    category_filter: str | None = None  # filter berdasarkan category metadata
    score_threshold: float = 0.7        # minimum similarity score
```

### Output: Retrieval

```python
class RetrievalResult:
    chunks: list[RetrievedChunk]
    query: str
    total_found: int                    # sebelum filtering
    total_after_filter: int             # setelah threshold filtering

class RetrievedChunk:
    text: str                           # konten chunk
    score: float                        # similarity score (0.0 - 1.0)
    metadata: ChunkMetadata

class ChunkMetadata:
    source: str                         # nama file asal
    category: str                       # tor_template / tor_example / guideline
    chunk_index: int                    # urutan chunk dalam dokumen asal
    total_chunks: int                   # total chunk dari dokumen asal
```

### Output: Formatted Context String (untuk prompt injection)

```
## REFERENSI (Gunakan sebagai inspirasi jika relevan, abaikan jika tidak)

Berikut adalah contoh/template TOR yang mungkin relevan dengan kebutuhan user:

---
[Referensi 1: tor_workshop_ai_2025.md (similarity: 0.89)]
Workshop ini bertujuan untuk meningkatkan kompetensi peserta dalam
memanfaatkan teknologi AI generatif. Peserta akan mendapatkan...
---
[Referensi 2: template_workshop.md (similarity: 0.82)]
## Latar Belakang
Kegiatan workshop ini diselenggarakan dalam rangka...
---
[Referensi 3: guideline_bahasa_formal.md (similarity: 0.74)]
Dokumen TOR harus menggunakan bahasa Indonesia baku...
---

Catatan: Referensi di atas hanya sebagai panduan style dan detail.
```

---

## 4. Flow Logic

### 4A. Ingestion Flow (Dokumen → Vector DB)

```
STEP 1: LOAD DOCUMENTS
────────────────────────
Input: folder path ATAU uploaded files
    │
    ├─► Untuk setiap file:
    │    ├─► Baca content (UTF-8)
    │    ├─► Deteksi format: .md → markdown, .txt → plain text
    │    ├─► Generate document_id: hash(filename + content[:100])
    │    └─► Buat Document(
    │            id=document_id,
    │            content=raw_text,
    │            metadata={
    │                "source": filename,
    │                "category": category,
    │                "file_type": "md" | "txt",
    │                "char_count": len(raw_text),
    │                "loaded_at": datetime.utcnow()
    │            }
    │        )
    │
    └─► Output: List[Document]

STEP 2: SPLIT INTO CHUNKS
──────────────────────────
Input: List[Document]
    │
    ├─► Untuk setiap Document:
    │    ├─► TextSplitter.split(
    │    │       text=document.content,
    │    │       chunk_size=500,        # karakter
    │    │       chunk_overlap=50,      # karakter overlap
    │    │       separators=["\n## ", "\n### ", "\n\n", "\n", ". "]
    │    │   )
    │    │
    │    ├─► Untuk setiap chunk:
    │    │    └─► Buat Chunk(
    │    │            id=f"{document_id}_chunk_{i}",
    │    │            text=chunk_text,
    │    │            metadata={
    │    │                **document.metadata,
    │    │                "chunk_index": i,
    │    │                "total_chunks": total,
    │    │                "char_count": len(chunk_text)
    │    │            }
    │    │        )
    │    │
    │    └─► Validasi: skip chunks < 50 karakter (terlalu pendek)
    │
    └─► Output: List[Chunk]

STEP 3: GENERATE EMBEDDINGS
─────────────────────────────
Input: List[Chunk]
    │
    ├─► Batch processing (max 32 chunks per batch)
    │
    ├─► Untuk setiap batch:
    │    ├─► texts = [chunk.text for chunk in batch]
    │    ├─► Panggil Ollama embedding API:
    │    │       POST http://localhost:11434/api/embed
    │    │       body: { "model": "bge-m3", "input": texts }
    │    │       → Response: { "embeddings": [[float, ...], ...] }
    │    │
    │    └─► Pair setiap embedding dengan chunk-nya
    │
    └─► Output: List[(Chunk, List[float])]

STEP 4: UPSERT TO VECTOR DB
──────────────────────────────
Input: List[(Chunk, Embedding)]
    │
    ├─► ChromaDB collection: "tor_documents"
    │
    ├─► collection.upsert(
    │       ids=[chunk.id for chunk in chunks],
    │       embeddings=[emb for _, emb in pairs],
    │       documents=[chunk.text for chunk in chunks],
    │       metadatas=[chunk.metadata for chunk in chunks]
    │   )
    │
    └─► Output: IngestResult(ingested=m, chunks=n, collection_size=total)
```

### 4B. Retrieval Flow (Query → Context)

```
STEP 1: EMBED QUERY
─────────────────────
Input: query string (e.g., user message or TOR title)
    │
    ├─► Panggil Ollama:
    │       POST http://localhost:11434/api/embed
    │       body: { "model": "bge-m3", "input": [query] }
    │       → query_embedding: List[float]
    │
    └─► Output: query_embedding

STEP 2: SIMILARITY SEARCH
───────────────────────────
Input: query_embedding, top_k, category_filter
    │
    ├─► where_filter = {}
    │   IF category_filter:
    │       where_filter = {"category": category_filter}
    │
    ├─► results = collection.query(
    │       query_embeddings=[query_embedding],
    │       n_results=top_k * 2,        # ambil lebih banyak untuk filtering
    │       where=where_filter if where_filter else None,
    │       include=["documents", "metadatas", "distances"]
    │   )
    │
    └─► Output: raw results (ids, documents, distances, metadatas)

STEP 3: SCORE FILTERING
─────────────────────────
Input: raw results
    │
    ├─► ChromaDB returns "distances" (cosine), convert ke similarity:
    │       similarity = 1 - distance
    │
    ├─► Filter: keep only similarity >= score_threshold (0.7)
    │
    ├─► Sort by similarity descending
    │
    ├─► Take top_k results
    │
    └─► Output: List[RetrievedChunk]

STEP 4: FORMAT CONTEXT
───────────────────────
Input: List[RetrievedChunk]
    │
    ├─► IF len(chunks) == 0:
    │       return None  # tidak ada referensi relevan
    │
    ├─► Compose formatted string:
    │       header + per-chunk reference block + footer
    │
    └─► Output: formatted_context: str
```

---

## 5. Data Structure

### 5.1 Document (dokumen sumber)

```python
class Document(BaseModel):
    id: str                          # hash-based ID
    content: str                     # raw text content
    metadata: DocumentMetadata

class DocumentMetadata(BaseModel):
    source: str                      # filename
    category: str                    # "tor_template" | "tor_example" | "guideline"
    file_type: str                   # "md" | "txt"
    char_count: int
    loaded_at: datetime
```

### 5.2 Chunk (potongan dokumen)

```python
class Chunk(BaseModel):
    id: str                          # "{doc_id}_chunk_{index}"
    text: str                        # chunk content
    metadata: ChunkMetadata

class ChunkMetadata(BaseModel):
    source: str                      # nama file asal
    category: str
    file_type: str
    chunk_index: int                 # 0-based
    total_chunks: int                # total chunks dari dokumen asal
    char_count: int
    loaded_at: datetime
```

### 5.3 RetrievedChunk (hasil retrieval)

```python
class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float                     # similarity score (0.0 - 1.0)
    metadata: ChunkMetadata
```

### 5.4 ChromaDB Collection Schema

```
Collection: "tor_documents"
├── ids: List[str]           → Chunk.id
├── embeddings: List[List[float]]  → 1024-dim vectors (bge-m3)
├── documents: List[str]     → Chunk.text
└── metadatas: List[dict]    → Chunk.metadata (source, category, index, etc.)
```

### 5.5 SQLite Table (tracking dokumen yang sudah di-ingest)

```sql
CREATE TABLE rag_documents (
    id TEXT PRIMARY KEY,               -- document hash ID
    filename TEXT NOT NULL,
    category TEXT NOT NULL,
    file_type TEXT NOT NULL,
    char_count INTEGER,
    chunk_count INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(filename, category)         -- prevent duplicate ingest
);
```

---

## 6. API Contract

### 6.1 `POST /api/v1/rag/ingest`

**Deskripsi**: Upload dan index dokumen ke vector DB.

**Request** (`multipart/form-data`):

| Field | Type | Required | Keterangan |
|---|---|---|---|
| `files` | `UploadFile[]` | ✅ | File `.md` atau `.txt`. Max 10 file per request. Max 1MB per file. |
| `category` | `string` | ✅ | `"tor_template"`, `"tor_example"`, atau `"guideline"` |

**Request contoh (cURL)**:
```bash
curl -X POST http://localhost:8000/api/v1/rag/ingest \
  -F "files=@data/documents/examples/tor_workshop_ai.md" \
  -F "files=@data/documents/examples/tor_pengadaan_server.md" \
  -F "category=tor_example"
```

**Response (200 OK)**:
```json
{
    "status": "success",
    "ingested_files": 2,
    "total_chunks": 35,
    "collection_size": 89,
    "details": [
        {
            "filename": "tor_workshop_ai.md",
            "chunks": 18,
            "char_count": 4520,
            "status": "ingested"
        },
        {
            "filename": "tor_pengadaan_server.md",
            "chunks": 17,
            "char_count": 3890,
            "status": "ingested"
        }
    ]
}
```

**Response (400 Bad Request) — File format tidak didukung**:
```json
{
    "error": {
        "code": "E009",
        "message": "Format file tidak didukung: proposal.pdf. Gunakan .md atau .txt",
        "supported_formats": [".md", ".txt"]
    }
}
```

---

### 6.2 `GET /api/v1/rag/status`

**Deskripsi**: Informasi status vector database.

**Response (200 OK)**:
```json
{
    "status": "healthy",
    "vector_db": {
        "type": "chromadb",
        "collection": "tor_documents",
        "total_documents": 8,
        "total_chunks": 156,
        "embedding_model": "bge-m3",
        "embedding_dimensions": 1024
    },
    "documents": [
        {
            "filename": "tor_workshop_ai.md",
            "category": "tor_example",
            "chunks": 18,
            "ingested_at": "2026-04-18T12:00:00Z"
        }
    ]
}
```

---

## 7. Dependencies

### Dependency ke modul lain

| Modul | Interface | Wajib? |
|---|---|---|
| **beta0.1.0 (Chat Engine)** | `OllamaProvider.embed()` — shared embedding call | ✅ |
| **beta0.1.4 (API Layer)** | Endpoint di-register ke router | ✅ |

### Interface yang disediakan untuk modul lain

```python
class RAGPipeline:
    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
        category_filter: str | None = None,
        score_threshold: float = 0.7
    ) -> str | None:
        """Retrieve relevant context dan return sebagai formatted string."""
        ...

    async def retrieve_raw(self, ...) -> list[RetrievedChunk]:
        """Retrieve chunks tanpa formatting."""
        ...

    async def ingest_files(self, file_paths: list[str], category: str) -> IngestResult:
        """Ingest file dari filesystem."""
        ...

    async def get_status(self) -> RAGStatus:
        """Get vector DB status and document list."""
        ...
```

### Library dependencies (Python packages)

```
chromadb>=0.5.0                    # Vector database
langchain-text-splitters>=0.3.0    # Text chunking utility
ollama>=0.4.0                      # Shared — embedding model via Ollama
python-multipart>=0.0.9            # File upload handling
aiosqlite>=0.20.0                  # Shared — tracking ingested docs
```

### External dependencies

| Service | Versi | Install |
|---|---|---|
| Ollama | >= 0.3.0 | (sudah dari beta0.1.0) |
| Model bge-m3 | latest | `ollama pull bge-m3` |

---

## 8. Pseudocode

### 8.1 DocumentLoader

```python
import hashlib
from pathlib import Path
from datetime import datetime

class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".md", ".txt"}

    def load_from_directory(self, dir_path: str, category: str) -> list[Document]:
        documents = []
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Directory tidak ditemukan: {dir_path}")
        for file_path in path.rglob("*"):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                doc = self._load_file(file_path, category)
                documents.append(doc)
        return documents

    def load_from_upload(self, filename: str, content: bytes, category: str) -> Document:
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFormatError(filename, self.SUPPORTED_EXTENSIONS)
        text = content.decode("utf-8")
        return self._create_document(filename, text, ext, category)

    def _create_document(self, filename: str, text: str, ext: str, category: str) -> Document:
        doc_id = hashlib.sha256(f"{filename}:{text[:100]}".encode()).hexdigest()[:16]
        return Document(
            id=doc_id,
            content=text,
            metadata=DocumentMetadata(
                source=filename,
                category=category,
                file_type=ext.lstrip("."),
                char_count=len(text),
                loaded_at=datetime.utcnow()
            )
        )
```

### 8.2 TextSplitter

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextChunker:
    def __init__(self, chunk_size=500, chunk_overlap=50, min_chunk_size=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
            keep_separator=True,
        )
        self.min_chunk_size = min_chunk_size

    def split(self, document: Document) -> list[Chunk]:
        raw_chunks = self.splitter.split_text(document.content)
        valid_chunks = [c for c in raw_chunks if len(c.strip()) >= self.min_chunk_size]
        chunks = []
        for i, text in enumerate(valid_chunks):
            chunk = Chunk(
                id=f"{document.id}_chunk_{i}",
                text=text.strip(),
                metadata=ChunkMetadata(
                    source=document.metadata.source,
                    category=document.metadata.category,
                    file_type=document.metadata.file_type,
                    chunk_index=i,
                    total_chunks=len(valid_chunks),
                    char_count=len(text.strip()),
                    loaded_at=document.metadata.loaded_at,
                )
            )
            chunks.append(chunk)
        return chunks
```

### 8.3 Embedder (via Ollama)

```python
import ollama

class OllamaEmbedder:
    def __init__(self, model: str = "bge-m3", base_url: str = "http://localhost:11434"):
        self.client = ollama.AsyncClient(host=base_url)
        self.model = model
        self.batch_size = 32

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            response = await self.client.embed(model=self.model, input=batch)
            all_embeddings.extend(response["embeddings"])
        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        response = await self.client.embed(model=self.model, input=[query])
        return response["embeddings"][0]
```

### 8.4 VectorStore (ChromaDB Wrapper)

```python
import chromadb

class ChromaVectorStore:
    COLLECTION_NAME = "tor_documents"

    def __init__(self, persist_path: str = "./data/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, ids, embeddings, documents, metadatas):
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

    def query(self, query_embedding, n_results=6, where=None) -> dict:
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        return self.collection.query(**kwargs)

    def count(self) -> int:
        return self.collection.count()

    def delete_by_source(self, source: str):
        self.collection.delete(where={"source": source})

    def get_all_sources(self) -> list[dict]:
        results = self.collection.get(include=["metadatas"])
        sources = {}
        for meta in results["metadatas"]:
            src = meta["source"]
            if src not in sources:
                sources[src] = {"source": src, "category": meta["category"], "chunks": 0}
            sources[src]["chunks"] += 1
        return list(sources.values())
```

### 8.5 Retriever

```python
class Retriever:
    def __init__(self, vector_store, embedder, default_top_k=3, default_threshold=0.7):
        self.store = vector_store
        self.embedder = embedder
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold

    async def retrieve(self, query, top_k=None, category_filter=None, score_threshold=None):
        top_k = top_k or self.default_top_k
        score_threshold = score_threshold or self.default_threshold

        query_embedding = await self.embedder.embed_query(query)
        where = {"category": category_filter} if category_filter else None
        raw_results = self.store.query(query_embedding=query_embedding, n_results=top_k * 2, where=where)

        chunks = []
        if raw_results.get("ids") and raw_results["ids"][0]:
            for i, doc_id in enumerate(raw_results["ids"][0]):
                distance = raw_results["distances"][0][i]
                similarity = 1 - distance  # cosine distance → similarity
                if similarity >= score_threshold:
                    chunks.append(RetrievedChunk(
                        id=doc_id,
                        text=raw_results["documents"][0][i],
                        score=round(similarity, 4),
                        metadata=ChunkMetadata(**raw_results["metadatas"][0][i]),
                    ))

        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks[:top_k]
```

### 8.6 ContextFormatter

```python
class ContextFormatter:
    TEMPLATE_HEADER = (
        "## REFERENSI (Gunakan sebagai inspirasi jika relevan, abaikan jika tidak)\n\n"
        "Berikut adalah contoh/template TOR yang mungkin relevan dengan kebutuhan user:\n"
    )
    TEMPLATE_FOOTER = (
        "\nCatatan: Referensi di atas hanya sebagai panduan style dan detail. "
        "Sesuaikan dengan kebutuhan spesifik user."
    )

    @staticmethod
    def format(chunks: list[RetrievedChunk]) -> str | None:
        if not chunks:
            return None
        parts = [ContextFormatter.TEMPLATE_HEADER]
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"\n---\n"
                f"[Referensi {i}: {chunk.metadata.source} "
                f"(similarity: {chunk.score:.2f})]\n"
                f"{chunk.text}\n"
            )
        parts.append(f"---\n{ContextFormatter.TEMPLATE_FOOTER}")
        return "\n".join(parts)
```

### 8.7 RAGPipeline — Orchestrator

```python
class RAGPipeline:
    def __init__(self, loader, chunker, embedder, store, retriever, formatter):
        self.loader = loader
        self.chunker = chunker
        self.embedder = embedder
        self.store = store
        self.retriever = retriever
        self.formatter = formatter

    async def ingest_files(self, file_paths: list[str], category: str) -> IngestResult:
        documents = [self.loader._load_file_by_path(fp, category) for fp in file_paths]
        all_chunks = []
        details = []
        for doc in documents:
            chunks = self.chunker.split(doc)
            all_chunks.extend(chunks)
            details.append({"filename": doc.metadata.source, "chunks": len(chunks), "status": "ingested"})
        if all_chunks:
            texts = [c.text for c in all_chunks]
            embeddings = await self.embedder.embed_texts(texts)
            self.store.upsert(
                ids=[c.id for c in all_chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c.metadata.model_dump() for c in all_chunks],
            )
        return IngestResult(status="success", ingested_files=len(documents),
                            total_chunks=len(all_chunks), collection_size=self.store.count(),
                            details=details)

    async def retrieve(self, query, top_k=3, category_filter=None, score_threshold=0.7) -> str | None:
        chunks = await self.retriever.retrieve(
            query=query, top_k=top_k, category_filter=category_filter, score_threshold=score_threshold
        )
        return self.formatter.format(chunks)

    async def get_status(self) -> dict:
        sources = self.store.get_all_sources()
        return {
            "status": "healthy",
            "vector_db": {
                "type": "chromadb",
                "collection": ChromaVectorStore.COLLECTION_NAME,
                "total_chunks": self.store.count(),
                "total_documents": len(sources),
                "embedding_model": self.embedder.model,
            },
            "documents": sources,
        }
```

---

## 9. Edge Cases

### Edge Case 1: Ollama Embedding Model Belum Di-pull

**Trigger**: `bge-m3` belum di-pull.

**Handling**:
```python
except ollama.ResponseError as e:
    if "model" in str(e).lower() and "not found" in str(e).lower():
        raise EmbeddingModelError(self.embedder.model)
    raise
```

### Edge Case 2: File Upload Format Tidak Didukung

**Trigger**: User upload `.pdf`, `.docx`

**Handling**: Return HTTP 400 dengan code `E009`.

### Edge Case 3: Dokumen Terlalu Kecil (< 50 Karakter)

**Handling**: Skip chunk, log warning, return status `"skipped"` di detail.

### Edge Case 4: ChromaDB Path Tidak Accessible

**Handling**: Raise `VectorDBError` saat inisialisasi.

### Edge Case 5: Tidak Ada Chunk Relevan

**Handling**: `retrieve()` return `None` — ChatService lanjut tanpa RAG context.

### Edge Case 6: Duplicate Ingest

**Handling**: ChromaDB `upsert` overwrite otomatis jika ID sama. SQLite ON CONFLICT DO UPDATE.

---

## 10. File yang Harus Dibuat

```
app/
├── rag/
│   ├── __init__.py
│   ├── document_loader.py        # DocumentLoader class
│   ├── text_splitter.py          # TextChunker class
│   ├── embedder.py               # OllamaEmbedder class
│   ├── vector_store.py           # ChromaVectorStore class
│   ├── retriever.py              # Retriever class
│   ├── context_formatter.py      # ContextFormatter class
│   └── pipeline.py               # RAGPipeline orchestrator
│
├── api/routes/
│   └── rag.py                    # POST /api/v1/rag/ingest + GET /api/v1/rag/status
│
├── models/
│   └── rag.py                    # Document, Chunk, RetrievedChunk, IngestResult

scripts/
└── ingest_documents.py           # CLI batch ingest

data/
└── documents/
    ├── templates/
    │   └── template_workshop.md
    ├── examples/
    │   └── tor_workshop_ai_2025.md
    └── guidelines/
        └── guideline_bahasa_formal.md
```

---

## 11. Cara Test Modul Ini Secara Standalone

```bash
# 1. Pull embedding model
ollama pull bge-m3

# 2. Siapkan contoh dokumen
mkdir -p data/documents/examples
echo "# TOR Workshop AI\n## Latar Belakang\nWorkshop ini..." > data/documents/examples/contoh_tor.md

# 3. Jalankan server
uvicorn app.main:app --reload --port 8000

# 4. Ingest via API
curl -X POST http://localhost:8000/api/v1/rag/ingest \
  -F "files=@data/documents/examples/contoh_tor.md" \
  -F "category=tor_example"

# 5. Cek status RAG
curl http://localhost:8000/api/v1/rag/status

# 6. Batch ingest via CLI script
python scripts/ingest_documents.py --dir data/documents/ --category tor_example
```
