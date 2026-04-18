# Task 04 — Text Chunker (Document Splitter)

## 1. Judul Task

Implementasi `TextChunker` — split dokumen menjadi potongan teks (chunks) yang optimal untuk embedding dan retrieval.

## 2. Deskripsi

Membuat class `TextChunker` yang memecah isi `Document` menjadi list `Chunk` menggunakan `RecursiveCharacterTextSplitter` dari `langchain-text-splitters`. Setiap chunk memiliki metadata lengkap (source, category, index) dan chunks yang terlalu pendek (< min_chunk_size) dibuang.

## 3. Tujuan Teknis

- `TextChunker.split(document)` → `list[Chunk]`
- Hierarchical separators: `\n## ` → `\n### ` → `\n\n` → `\n` → `. ` → ` `
- Skip chunks dengan panjang `< min_chunk_size` (default 50 chars)
- Chunk ID format: `{document_id}_chunk_{index}`

## 4. Scope

### Yang dikerjakan
- `app/rag/text_splitter.py` — class `TextChunker`

### Yang tidak dikerjakan
- Embedding (itu task 05)
- Loading dokumen (itu task 03)

## 5. Langkah Implementasi

### Step 1: Install dependency

Pastikan `langchain-text-splitters` sudah ada di `requirements.txt`. Tambahkan jika belum:
```
langchain-text-splitters>=0.3.0
```

Lalu install:
```bash
.\venv\Scripts\pip.exe install langchain-text-splitters>=0.3.0
```

### Step 2: Buat `app/rag/text_splitter.py`

```python
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.rag import Document, Chunk, ChunkMetadata

logger = logging.getLogger("ai-agent-hybrid.rag.splitter")


class TextChunker:
    """Split dokumen menjadi chunks yang siap di-embed."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 50,
    ):
        self.min_chunk_size = min_chunk_size
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
            keep_separator=True,
        )

    def split(self, document: Document) -> list[Chunk]:
        """Split satu Document menjadi list Chunk."""
        raw_chunks = self.splitter.split_text(document.content)

        # Filter chunks yang terlalu pendek
        valid_texts = [c for c in raw_chunks if len(c.strip()) >= self.min_chunk_size]

        if not valid_texts:
            logger.warning(
                f"Document '{document.metadata.source}' menghasilkan 0 valid chunks "
                f"(min_chunk_size={self.min_chunk_size})"
            )
            return []

        chunks = []
        for i, text in enumerate(valid_texts):
            chunk = Chunk(
                id=f"{document.id}_chunk_{i}",
                text=text.strip(),
                metadata=ChunkMetadata(
                    source=document.metadata.source,
                    category=document.metadata.category,
                    file_type=document.metadata.file_type,
                    chunk_index=i,
                    total_chunks=len(valid_texts),
                    char_count=len(text.strip()),
                    loaded_at=document.metadata.loaded_at,
                ),
            )
            chunks.append(chunk)

        logger.debug(
            f"Split '{document.metadata.source}' → {len(chunks)} chunks "
            f"(dari {len(raw_chunks)} raw, {len(raw_chunks)-len(valid_texts)} dibuang)"
        )
        return chunks

    def split_many(self, documents: list[Document]) -> list[Chunk]:
        """Split banyak dokumen sekaligus."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.split(doc))
        return all_chunks
```

### Step 3: Verifikasi

```python
from datetime import datetime
from app.models.rag import Document, DocumentMetadata
from app.rag.text_splitter import TextChunker

# Buat dokumen test
content = """# TOR Workshop AI

## Latar Belakang
Workshop ini bertujuan meningkatkan kompetensi ASN dalam bidang kecerdasan buatan.
Kegiatan ini diselenggarakan oleh Badan Pengembangan SDM.

## Tujuan
Setelah pelatihan, peserta mampu:
1. Memahami konsep dasar AI
2. Menggunakan tools AI generatif
3. Menerapkan AI dalam pekerjaan sehari-hari

## Ruang Lingkup
Pelatihan 3 hari untuk 30 peserta ASN di Jakarta Pusat.

## Output
- Sertifikat kehadiran
- Modul pelatihan digital
- Akses platform learning selama 6 bulan

## Timeline
Bulan Juli 2026, 3 hari kerja (10-12 Juli 2026).
"""

meta = DocumentMetadata(
    source="tor_test.md", category="tor_example",
    file_type="md", char_count=len(content), loaded_at=datetime.utcnow()
)
doc = Document(id="testdoc1", content=content, metadata=meta)

chunker = TextChunker(chunk_size=300, chunk_overlap=30, min_chunk_size=50)
chunks = chunker.split(doc)

# Test 1: chunk dihasilkan
assert len(chunks) > 0
print(f"Test 1 passed: {len(chunks)} chunks generated")

# Test 2: chunk ID format benar
assert all(c.id.startswith("testdoc1_chunk_") for c in chunks)
print("Test 2 passed: chunk IDs correct")

# Test 3: metadata lengkap
assert chunks[0].metadata.source == "tor_test.md"
assert chunks[0].metadata.total_chunks == len(chunks)
assert chunks[0].metadata.chunk_index == 0
print("Test 3 passed: metadata complete")

# Test 4: tidak ada chunk pendek
assert all(len(c.text) >= 50 for c in chunks)
print("Test 4 passed: no short chunks")

# Test 5: dokumen terlalu pendek → 0 chunks
meta2 = DocumentMetadata(
    source="short.md", category="tor_example",
    file_type="md", char_count=10, loaded_at=datetime.utcnow()
)
doc2 = Document(id="shortdoc", content="Pendek.", metadata=meta2)
chunks2 = chunker.split(doc2)
assert chunks2 == []
print("Test 5 passed: too-short document handled")

print("ALL CHUNKER TESTS PASSED")
```

## 6. Output yang Diharapkan

```
Test 1 passed: N chunks generated
Test 2 passed: chunk IDs correct
Test 3 passed: metadata complete
Test 4 passed: no short chunks
Test 5 passed: too-short document handled
ALL CHUNKER TESTS PASSED
```

## 7. Dependencies

- **Task 01** — `Document`, `Chunk`, `ChunkMetadata` models
- **Task 03** — `DocumentLoader` (untuk integration test)

## 8. Acceptance Criteria

- [ ] `TextChunker().split(doc)` return list chunk tidak kosong untuk dokumen normal
- [ ] Setiap chunk ID format `"{doc_id}_chunk_{i}"`
- [ ] `chunk.metadata.total_chunks` sama dengan `len(chunks)` untuk semua chunk dalam dokumen
- [ ] `chunk.metadata.chunk_index` dimulai dari `0`
- [ ] Chunk dengan panjang `< 50 chars` tidak masuk hasil
- [ ] Dokumen terlalu pendek → return `[]` tanpa error
- [ ] `split_many([doc1, doc2])` menggabungkan chunks dari kedua dokumen

## 9. Estimasi

**Low** — ~1 jam
