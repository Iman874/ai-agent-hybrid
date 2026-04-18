# Task 07 — Retriever & Context Formatter

## 1. Judul Task

Implementasi `Retriever` (similarity search + score filtering) dan `ContextFormatter` (format chunks jadi context string).

## 2. Deskripsi

Membuat dua class:
1. `Retriever` — menerima query string, generate embedding, query ChromaDB, filter by score threshold, return `list[RetrievedChunk]`
2. `ContextFormatter` — konversi `list[RetrievedChunk]` menjadi formatted string yang siap di-inject ke prompt LLM

## 3. Tujuan Teknis

- `Retriever.retrieve(query, top_k, category_filter, score_threshold)` → `list[RetrievedChunk]`
- Konversi cosine distance ChromaDB → similarity: `similarity = 1 - distance`
- Filter: hanya chunks dengan `similarity >= score_threshold`
- `ContextFormatter.format(chunks)` → `str | None` (None jika tidak ada chunks)
- Format output sesuai template dari modul design

## 4. Scope

### Yang dikerjakan
- `app/rag/retriever.py` — class `Retriever`
- `app/rag/context_formatter.py` — class `ContextFormatter`

### Yang tidak dikerjakan
- Pipeline orchestration (itu task 08)
- Ingest flow (itu task 08)

## 5. Langkah Implementasi

### Step 1: Buat `app/rag/retriever.py`

```python
import logging
from app.models.rag import RetrievedChunk, ChunkMetadata
from app.rag.embedder import OllamaEmbedder
from app.rag.vector_store import ChromaVectorStore

logger = logging.getLogger("ai-agent-hybrid.rag.retriever")


class Retriever:
    """Retrieve relevant chunks dari vector store berdasarkan query."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embedder: OllamaEmbedder,
        default_top_k: int = 3,
        default_threshold: float = 0.7,
    ):
        self.store = vector_store
        self.embedder = embedder
        self.default_top_k = default_top_k
        self.default_threshold = default_threshold

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        category_filter: str | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve most relevant chunks untuk query.

        Args:
            query: Teks query (user message / judul TOR)
            top_k: Jumlah chunk yang dikembalikan
            category_filter: Filter berdasarkan category metadata
            score_threshold: Minimum similarity score (0.0 - 1.0)

        Returns:
            List RetrievedChunk, diurutkan descending by score
        """
        top_k = top_k or self.default_top_k
        score_threshold = score_threshold or self.default_threshold

        # Step 1: Embed query
        logger.debug(f"Embedding query: '{query[:50]}...'")
        query_embedding = await self.embedder.embed_query(query)

        # Step 2: Query vector DB (ambil lebih banyak untuk filtering)
        where = {"category": category_filter} if category_filter else None
        raw_results = self.store.query(
            query_embedding=query_embedding,
            n_results=top_k * 2,
            where=where,
        )

        # Step 3: Convert distances → similarity scores & filter
        chunks = []
        if raw_results.get("ids") and raw_results["ids"][0]:
            for i, doc_id in enumerate(raw_results["ids"][0]):
                distance = raw_results["distances"][0][i]
                similarity = 1 - distance  # cosine distance → similarity

                if similarity >= score_threshold:
                    raw_meta = raw_results["metadatas"][0][i]
                    chunks.append(RetrievedChunk(
                        id=doc_id,
                        text=raw_results["documents"][0][i],
                        score=round(similarity, 4),
                        metadata=ChunkMetadata(**raw_meta),
                    ))

        # Sort descending by score, limit to top_k
        chunks.sort(key=lambda c: c.score, reverse=True)
        result = chunks[:top_k]

        logger.info(
            f"Retrieved {len(result)} chunks "
            f"(threshold={score_threshold}, filter={category_filter})"
        )
        return result
```

### Step 2: Buat `app/rag/context_formatter.py`

```python
import logging
from app.models.rag import RetrievedChunk

logger = logging.getLogger("ai-agent-hybrid.rag.formatter")


class ContextFormatter:
    """Format retrieved chunks menjadi context string untuk prompt injection."""

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
        """
        Format list chunks menjadi context string.

        Returns:
            Formatted string atau None jika chunks kosong
        """
        if not chunks:
            logger.debug("No chunks to format, returning None")
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
        context = "\n".join(parts)
        logger.debug(f"Formatted {len(chunks)} chunks → {len(context)} chars")
        return context
```

### Step 3: Verifikasi (ContextFormatter saja, tanpa Ollama)

```python
from datetime import datetime
from app.models.rag import RetrievedChunk, ChunkMetadata
from app.rag.context_formatter import ContextFormatter

# Buat dummy chunks
def make_chunk(i, score):
    return RetrievedChunk(
        id=f"chunk_{i}",
        text=f"Ini adalah teks referensi nomor {i} dari dokumen TOR workshop.",
        score=score,
        metadata=ChunkMetadata(
            source=f"tor_{i}.md", category="tor_example",
            file_type="md", chunk_index=0, total_chunks=3,
            char_count=50, loaded_at=datetime.utcnow()
        )
    )

# Test 1: Format 3 chunks
chunks = [make_chunk(1, 0.92), make_chunk(2, 0.84), make_chunk(3, 0.76)]
context = ContextFormatter.format(chunks)
assert context is not None
assert "REFERENSI" in context
assert "Referensi 1" in context
assert "similarity: 0.92" in context
print("Test 1 passed: format 3 chunks OK")

# Test 2: Empty list → None
result = ContextFormatter.format([])
assert result is None
print("Test 2 passed: empty → None")

# Test 3: Structure check
assert context.startswith("## REFERENSI")
assert "Catatan:" in context
print("Test 3 passed: structure correct")

print(f"Sample output:\n{context[:300]}...")
print("ALL FORMATTER TESTS PASSED")
```

## 6. Output yang Diharapkan

```
Test 1 passed: format 3 chunks OK
Test 2 passed: empty → None
Test 3 passed: structure correct
Sample output:
## REFERENSI (Gunakan sebagai inspirasi jika relevan, abaikan jika tidak)

Berikut adalah contoh/template TOR yang mungkin relevan dengan kebutuhan user:

---
[Referensi 1: tor_1.md (similarity: 0.92)]
Ini adalah teks referensi nomor 1 dari...
ALL FORMATTER TESTS PASSED
```

## 7. Dependencies

- **Task 01** — `RetrievedChunk`, `ChunkMetadata`
- **Task 05** — `OllamaEmbedder`
- **Task 06** — `ChromaVectorStore`

## 8. Acceptance Criteria

- [ ] `Retriever.retrieve("test query")` return `list[RetrievedChunk]` (membutuhkan Ollama)
- [ ] Hanya chunks dengan `score >= threshold` yang masuk hasil
- [ ] Chunks diurutkan descending by score
- [ ] `category_filter="tor_example"` hanya return chunk dari category tersebut
- [ ] `ContextFormatter.format([])` return `None`
- [ ] `ContextFormatter.format([chunk1, chunk2])` return string dengan header, body, footer
- [ ] Format output mengandung `"similarity: 0.XX"` untuk setiap chunk

## 9. Estimasi

**Medium** — ~1.5 jam
