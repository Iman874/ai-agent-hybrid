# Task 06 — ChromaDB Vector Store

## 1. Judul Task

Implementasi `ChromaVectorStore` — wrapper ChromaDB untuk upsert, query, dan manajemen vektor.

## 2. Deskripsi

Membuat class `ChromaVectorStore` sebagai wrapper bersih di atas ChromaDB. Mengelola collection `tor_documents` (cosine similarity), mendukung upsert batch, similarity query, delete by source, dan status check. Raise `VectorDBError` jika ChromaDB tidak bisa diinisialisasi.

## 3. Tujuan Teknis

- `upsert(ids, embeddings, documents, metadatas)` — simpan chunk ke ChromaDB
- `query(query_embedding, n_results, where)` — similarity search
- `count()` — total chunks di collection
- `delete_by_source(source)` — hapus semua chunk dari satu file
- `get_all_sources()` — list semua file yang sudah di-ingest
- Persist di `data/chroma_db/` (configurable)

## 4. Scope

### Yang dikerjakan
- `app/rag/vector_store.py` — class `ChromaVectorStore`

### Yang tidak dikerjakan
- Retrieval logic dengan score filtering (itu task 07)
- Database migration SQLite (itu task 09)

## 5. Langkah Implementasi

### Step 1: Install dependency

Tambahkan ke `requirements.txt`:
```
chromadb>=0.5.0
```

```bash
.\venv\Scripts\pip.exe install "chromadb>=0.5.0"
```

### Step 2: Buat `app/rag/vector_store.py`

```python
import logging
import chromadb

from app.config import Settings
from app.utils.errors import VectorDBError

logger = logging.getLogger("ai-agent-hybrid.rag.vector_store")


class ChromaVectorStore:
    """Wrapper ChromaDB untuk manajemen vector embeddings."""

    COLLECTION_NAME = "tor_documents"

    def __init__(self, settings: Settings):
        self.persist_path = settings.chroma_db_path
        self.collection_name = settings.chroma_collection_name

        try:
            self.client = chromadb.PersistentClient(path=self.persist_path)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # cosine similarity
            )
            logger.info(
                f"ChromaDB initialized: path={self.persist_path}, "
                f"collection={self.collection_name}, "
                f"total_chunks={self.collection.count()}"
            )
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise VectorDBError(
                f"Tidak dapat menginisialisasi ChromaDB di '{self.persist_path}'. Error: {e}"
            )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """Upsert chunks ke collection (add jika baru, update jika sudah ada)."""
        if not ids:
            return

        # ChromaDB max 5000 per upsert
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

        logger.debug(f"Upserted {len(ids)} chunks")

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 6,
        where: dict | None = None,
    ) -> dict:
        """
        Query collection untuk chunks yang paling similar.

        Returns: dict dengan keys: ids, documents, metadatas, distances
        """
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, self.collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        return self.collection.query(**kwargs)

    def count(self) -> int:
        """Total chunks di collection."""
        return self.collection.count()

    def delete_by_source(self, source: str) -> None:
        """Hapus semua chunks dari satu file (untuk re-ingest)."""
        try:
            self.collection.delete(where={"source": source})
            logger.info(f"Deleted chunks for source: {source}")
        except Exception as e:
            logger.warning(f"Delete by source failed for '{source}': {e}")

    def get_all_sources(self) -> list[dict]:
        """List semua dokumen yang sudah di-ingest beserta jumlah chunk-nya."""
        if self.collection.count() == 0:
            return []

        results = self.collection.get(include=["metadatas"])
        sources: dict[str, dict] = {}

        for meta in results["metadatas"]:
            src = meta["source"]
            if src not in sources:
                sources[src] = {
                    "source": src,
                    "category": meta.get("category", "unknown"),
                    "chunks": 0,
                }
            sources[src]["chunks"] += 1

        return list(sources.values())
```

### Step 3: Verifikasi (unit test dengan temp path)

```python
import asyncio
import os
import shutil
from app.config import Settings
from app.rag.vector_store import ChromaVectorStore

# Setup: gunakan temp path
import os
os.environ["CHROMA_DB_PATH"] = "./data/test_chroma"
settings = Settings()

store = ChromaVectorStore(settings)

# Test 1: Upsert chunks
store.upsert(
    ids=["chunk1", "chunk2"],
    embeddings=[[0.1] * 1024, [0.2] * 1024],  # dummy embeddings
    documents=["Teks pertama", "Teks kedua"],
    metadatas=[
        {"source": "test.md", "category": "tor_example", "chunk_index": 0},
        {"source": "test.md", "category": "tor_example", "chunk_index": 1},
    ]
)
assert store.count() == 2
print("Test 1 passed: upsert OK")

# Test 2: Query
results = store.query(query_embedding=[0.15] * 1024, n_results=2)
assert len(results["ids"][0]) == 2
print("Test 2 passed: query OK")

# Test 3: Count
assert store.count() >= 2
print(f"Test 3 passed: count={store.count()}")

# Test 4: Get all sources
sources = store.get_all_sources()
assert len(sources) >= 1
assert sources[0]["source"] == "test.md"
print(f"Test 4 passed: sources={sources}")

# Test 5: Delete by source
store.delete_by_source("test.md")
assert store.count() == 0
print("Test 5 passed: delete OK")

# Cleanup
shutil.rmtree("./data/test_chroma", ignore_errors=True)
print("ALL VECTOR STORE TESTS PASSED")
```

## 6. Output yang Diharapkan

```
ChromaDB initialized: path=./data/test_chroma, collection=tor_documents, total_chunks=0
Test 1 passed: upsert OK
Test 2 passed: query OK
Test 3 passed: count=2
Test 4 passed: sources=[{'source': 'test.md', 'category': 'tor_example', 'chunks': 2}]
Test 5 passed: delete OK
ALL VECTOR STORE TESTS PASSED
```

## 7. Dependencies

- **Task 01** — `VectorDBError`
- **Task 02** — `Settings.chroma_db_path`, `Settings.chroma_collection_name`

## 8. Acceptance Criteria

- [ ] `ChromaVectorStore(settings)` berhasil diinisialisasi tanpa error
- [ ] `upsert([...])` berhasil menyimpan chunks
- [ ] `count()` return jumlah chunk yang benar setelah upsert
- [ ] `query(embedding)` return hasil dengan keys `ids`, `documents`, `metadatas`, `distances`
- [ ] `delete_by_source("test.md")` menghapus semua chunk dari file tersebut
- [ ] `get_all_sources()` return list source yang benar
- [ ] Path persist bisa dikonfigurasi via `settings.chroma_db_path`
- [ ] Jika path tidak accessible → raise `VectorDBError`

## 9. Estimasi

**Medium** — ~1.5 jam
