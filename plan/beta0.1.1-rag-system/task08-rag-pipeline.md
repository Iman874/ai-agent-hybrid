# Task 08 — RAGPipeline Orchestrator

## 1. Judul Task

Implementasi `RAGPipeline` — orchestrator yang menghubungkan seluruh komponen RAG (Loader → Chunker → Embedder → VectorStore → Retriever → Formatter).

## 2. Deskripsi

Membuat class `RAGPipeline` yang menjadi single entry point untuk seluruh operasi RAG: `ingest_files()` untuk indexing dokumen baru, `retrieve()` untuk mendapatkan context string, `retrieve_raw()` untuk mendapatkan raw chunks, dan `get_status()` untuk status vector DB. Class ini di-wire di lifespan FastAPI dan dipakai oleh `ChatService`.

## 3. Tujuan Teknis

- `ingest_files(file_paths, category)` → `IngestResult` — full ingestion pipeline
- `ingest_from_uploads(uploads, category)` → `IngestResult` — dari uploaded bytes
- `retrieve(query, top_k, category_filter, score_threshold)` → `str | None`
- `retrieve_raw(...)` → `list[RetrievedChunk]`
- `get_status()` → dict (untuk API response)

## 4. Scope

### Yang dikerjakan
- `app/rag/pipeline.py` — class `RAGPipeline`
- `app/rag/__init__.py` — update exports

### Yang tidak dikerjakan
- API endpoints (itu task 10)
- SQLite tracking (itu task 09)

## 5. Langkah Implementasi

### Step 1: Buat `app/rag/pipeline.py`

```python
import logging
from app.config import Settings
from app.models.rag import IngestResult, IngestFileDetail, RetrievedChunk
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import TextChunker
from app.rag.embedder import OllamaEmbedder
from app.rag.vector_store import ChromaVectorStore
from app.rag.retriever import Retriever
from app.rag.context_formatter import ContextFormatter

logger = logging.getLogger("ai-agent-hybrid.rag.pipeline")


class RAGPipeline:
    """Orchestrator utama RAG System."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.loader = DocumentLoader()
        self.chunker = TextChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            min_chunk_size=settings.rag_min_chunk_size,
        )
        self.embedder = OllamaEmbedder(settings)
        self.store = ChromaVectorStore(settings)
        self.retriever = Retriever(
            vector_store=self.store,
            embedder=self.embedder,
            default_top_k=settings.rag_top_k,
            default_threshold=settings.rag_score_threshold,
        )
        self.formatter = ContextFormatter()

    async def ingest_files(
        self, file_paths: list[str], category: str
    ) -> IngestResult:
        """
        Ingest file dari filesystem.

        Args:
            file_paths: List path file yang akan di-ingest
            category: Kategori dokumen

        Returns:
            IngestResult dengan detail setiap file
        """
        logger.info(f"Starting ingest: {len(file_paths)} files, category={category}")

        all_chunks = []
        details = []

        for fpath in file_paths:
            try:
                # Load dokumen
                doc = self.loader._load_file_by_path(fpath, category)

                # Chunking
                chunks = self.chunker.split(doc)

                if not chunks:
                    details.append(IngestFileDetail(
                        filename=doc.metadata.source,
                        chunks=0,
                        char_count=doc.metadata.char_count,
                        status="skipped"
                    ))
                    continue

                all_chunks.extend(chunks)
                details.append(IngestFileDetail(
                    filename=doc.metadata.source,
                    chunks=len(chunks),
                    char_count=doc.metadata.char_count,
                    status="ingested"
                ))
            except Exception as e:
                logger.error(f"Failed to process {fpath}: {e}")
                details.append(IngestFileDetail(
                    filename=str(fpath).split("/")[-1],
                    chunks=0,
                    char_count=0,
                    status=f"error: {str(e)[:50]}"
                ))

        # Embed dan upsert semua chunks
        if all_chunks:
            texts = [c.text for c in all_chunks]
            embeddings = await self.embedder.embed_texts(texts)

            self.store.upsert(
                ids=[c.id for c in all_chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c.metadata.model_dump() for c in all_chunks],
            )

        result = IngestResult(
            status="success",
            ingested_files=sum(1 for d in details if d.status == "ingested"),
            total_chunks=len(all_chunks),
            collection_size=self.store.count(),
            details=details,
        )
        logger.info(
            f"Ingest complete: {result.ingested_files} files, "
            f"{result.total_chunks} chunks, total={result.collection_size}"
        )
        return result

    async def ingest_from_uploads(
        self,
        uploads: list[tuple[str, bytes]],  # list of (filename, content)
        category: str,
    ) -> IngestResult:
        """Ingest dari uploaded file bytes (dipakai oleh API endpoint)."""
        all_chunks = []
        details = []

        for filename, content in uploads:
            try:
                doc = self.loader.load_from_upload(filename, content, category)
                chunks = self.chunker.split(doc)

                if not chunks:
                    details.append(IngestFileDetail(
                        filename=filename, chunks=0,
                        char_count=doc.metadata.char_count, status="skipped"
                    ))
                    continue

                all_chunks.extend(chunks)
                details.append(IngestFileDetail(
                    filename=filename, chunks=len(chunks),
                    char_count=doc.metadata.char_count, status="ingested"
                ))
            except Exception as e:
                logger.error(f"Upload ingest failed for {filename}: {e}")
                details.append(IngestFileDetail(
                    filename=filename, chunks=0, char_count=0,
                    status=f"error: {str(e)[:50]}"
                ))

        if all_chunks:
            texts = [c.text for c in all_chunks]
            embeddings = await self.embedder.embed_texts(texts)
            self.store.upsert(
                ids=[c.id for c in all_chunks],
                embeddings=embeddings,
                documents=texts,
                metadatas=[c.metadata.model_dump() for c in all_chunks],
            )

        return IngestResult(
            status="success",
            ingested_files=sum(1 for d in details if d.status == "ingested"),
            total_chunks=len(all_chunks),
            collection_size=self.store.count(),
            details=details,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        score_threshold: float | None = None,
    ) -> str | None:
        """Retrieve dan return formatted context string. None jika tidak ada yang relevan."""
        chunks = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            category_filter=category_filter,
            score_threshold=score_threshold,
        )
        return self.formatter.format(chunks)

    async def retrieve_raw(
        self,
        query: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve tanpa formatting (untuk debugging/API response)."""
        return await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            category_filter=category_filter,
            score_threshold=score_threshold,
        )

    async def get_status(self) -> dict:
        """Status vector DB."""
        sources = self.store.get_all_sources()
        return {
            "status": "healthy",
            "vector_db": {
                "type": "chromadb",
                "collection": ChromaVectorStore.COLLECTION_NAME,
                "total_chunks": self.store.count(),
                "total_documents": len(sources),
                "embedding_model": self.settings.embedding_model,
                "embedding_dimensions": 1024,
            },
            "documents": sources,
        }
```

### Step 2: Update `app/rag/__init__.py`

```python
"""RAG Pipeline Module"""
from app.rag.pipeline import RAGPipeline
```

### Step 3: Update `DocumentLoader` untuk support path-based load

Tambahkan method di `DocumentLoader`:
```python
def _load_file_by_path(self, file_path: str, category: str) -> Document:
    """Load dari absolute/relative path."""
    from pathlib import Path
    path = Path(file_path)
    if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(path.name, self.SUPPORTED_EXTENSIONS)
    return self._load_file(path, category)
```

### Step 4: Verifikasi (requires Ollama + bge-m3)

```python
import asyncio
import os
import shutil

os.environ["CHROMA_DB_PATH"] = "./data/test_pipeline_chroma"

from app.config import Settings
from app.rag.pipeline import RAGPipeline

async def test():
    settings = Settings()
    pipeline = RAGPipeline(settings)

    # Test ingest dari upload
    content = b"""# TOR Workshop Machine Learning

## Latar Belakang
Kegiatan ini diselenggarakan untuk meningkatkan kapasitas ASN.

## Tujuan
Peserta mampu memahami algoritma machine learning dasar.

## Ruang Lingkup
Pelatihan 3 hari untuk 25 peserta di Bandung.

## Output
Sertifikat dan laporan proyek mini.

## Timeline
September 2026, 15-17 September.
"""
    result = await pipeline.ingest_from_uploads(
        uploads=[("test_tor.md", content)],
        category="tor_example"
    )
    assert result.ingested_files == 1
    assert result.total_chunks > 0
    print(f"Ingest OK: {result.total_chunks} chunks")

    # Test retrieve
    context = await pipeline.retrieve("workshop machine learning ASN")
    if context:
        print(f"Retrieve OK: {len(context)} chars")
        assert "REFERENSI" in context
    else:
        print("Retrieve OK: no match (threshold not met)")

    # Test status
    status = await pipeline.get_status()
    assert status["status"] == "healthy"
    assert status["vector_db"]["total_chunks"] > 0
    print(f"Status OK: {status['vector_db']}")

    # Cleanup
    shutil.rmtree("./data/test_pipeline_chroma", ignore_errors=True)
    print("ALL PIPELINE TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Ingest OK: N chunks
Retrieve OK: X chars (atau "no match")
Status OK: {'type': 'chromadb', 'total_chunks': N, ...}
ALL PIPELINE TESTS PASSED
```

## 7. Dependencies

- **Task 03** — `DocumentLoader`
- **Task 04** — `TextChunker`
- **Task 05** — `OllamaEmbedder`
- **Task 06** — `ChromaVectorStore`
- **Task 07** — `Retriever`, `ContextFormatter`

## 8. Acceptance Criteria

- [ ] `ingest_from_uploads([(filename, bytes)], category)` return `IngestResult` dengan `ingested_files >= 1`
- [ ] Setelah ingest, `store.count()` bertambah
- [ ] `retrieve(query)` return `str` atau `None`
- [ ] `retrieve_raw(query)` return `list[RetrievedChunk]`
- [ ] `get_status()` return dict dengan key `status`, `vector_db`, `documents`
- [ ] File yang terlalu pendek → status `"skipped"` di detail, tidak error
- [ ] File yang error saat load → status `"error: ..."` di detail, proses lanjut ke file berikutnya

## 9. Estimasi

**Medium** — ~2 jam
