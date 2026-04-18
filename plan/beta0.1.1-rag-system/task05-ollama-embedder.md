# Task 05 — Ollama Embedder

## 1. Judul Task

Implementasi `OllamaEmbedder` — generate embedding vektor menggunakan model `qwen3-embedding:0.6b` via Ollama API.

## 2. Deskripsi

Membuat class `OllamaEmbedder` yang memanggil Ollama embedding API (`/api/embed`) untuk mengkonversi teks menjadi vektor float. Mendukung batch processing (default 32 teks per batch) dan single-query embedding. Raise `EmbeddingModelError` jika model belum di-pull.

## 3. Tujuan Teknis

- `embed_texts(texts: list[str])` → `list[list[float]]` — batch embedding
- `embed_query(query: str)` → `list[float]` — single embedding
- Batch size configurable (default 32)
- Raise `EmbeddingModelError` jika model tidak ditemukan di Ollama

## 4. Scope

### Yang dikerjakan
- `app/rag/embedder.py` — class `OllamaEmbedder`

### Yang tidak dikerjakan
- ChromaDB integration (itu task 06)
- Pipeline orchestration (itu task 08)

## 5. Langkah Implementasi

### Step 1: Buat `app/rag/embedder.py`

```python
import logging
import ollama

from app.config import Settings
from app.utils.errors import EmbeddingModelError

logger = logging.getLogger("ai-agent-hybrid.rag.embedder")


class OllamaEmbedder:
    """Generate embeddings via Ollama qwen3-embedding:0.6b model."""

    def __init__(self, settings: Settings):
        self.client = ollama.AsyncClient(host=settings.ollama_base_url)
        self.model = settings.embedding_model
        self.batch_size = settings.embedding_batch_size

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # ... logic sama seperti bge-m3 ...
        pass

    async def embed_query(self, query: str) -> list[float]:
        # ... logic sama seperti bge-m3 ...
        pass
```

### Step 2: Verifikasi (membutuhkan Ollama + qwen3-embedding:0.6b running)

```bash
python test_embedder.py
```

### Step 3: Pull model (jika belum dilakukan)

```bash
ollama pull qwen3-embedding:0.6b
```

## 7. Dependencies

- **Task 02** — `EmbeddingModelError`, `Settings` dengan field `embedding_model`
- **Task 01 (beta0.1.0)** — `Settings.ollama_base_url`
- **External** — Ollama running + `ollama pull qwen3-embedding:0.6b`

## 8. Acceptance Criteria

- [ ] `embed_query("test")` return `list[float]`
- [ ] `embed_texts(["a", "b", "c"])` return list dengan 3 elemen
- [ ] Semua embedding dalam satu batch memiliki dimensi yang sama
- [ ] `embed_texts([])` return `[]` tanpa error
- [ ] Jika model belum di-pull → raise `EmbeddingModelError` (bukan generic exception)
- [ ] Batch dibagi otomatis jika jumlah teks > `batch_size`

## 9. Estimasi

**Low** — ~1 jam
