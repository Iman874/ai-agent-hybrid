# Task 09 — SQLite Tracking Table untuk RAG Documents

## 1. Judul Task

Tambahkan tabel `rag_documents` ke SQLite migration dan update `SessionManager` / `database.py` untuk tracking metadata dokumen yang sudah di-ingest.

## 2. Deskripsi

Membuat tabel `rag_documents` di SQLite untuk mencatat metadata setiap dokumen yang berhasil di-ingest (filename, category, chunk_count, ingested_at). Constraint `UNIQUE(filename, category)` mencegah duplicate entry. Digunakan oleh ingest endpoint untuk status reporting dan de-duplicate check.

## 3. Tujuan Teknis

- Tabel `rag_documents` dibuat via migration SQL baru (`002_rag_documents.sql`)
- `RAGDocumentTracker` — class untuk CRUD operasi tabel ini
- Duplicate check: jika file dengan name+category yang sama sudah ada → update, bukan insert baru
- `get_all()` → list metadata semua dokumen yang pernah di-ingest

## 4. Scope

### Yang dikerjakan
- `app/db/migrations/002_rag_documents.sql` — SQL migration
- `app/rag/document_tracker.py` — class `RAGDocumentTracker`

### Yang tidak dikerjakan
- Integrasi ke pipeline (itu task 08 – pipeline sudah bisa jalan tanpa tracking ini, tracking bersifat addon)
- ChromaDB operations

## 5. Langkah Implementasi

### Step 1: Buat `app/db/migrations/002_rag_documents.sql`

```sql
-- Migration 002: RAG Document Tracking Table
CREATE TABLE IF NOT EXISTS rag_documents (
    id TEXT PRIMARY KEY,               -- document hash ID (dari DocumentLoader)
    filename TEXT NOT NULL,
    category TEXT NOT NULL             CHECK(category IN ('tor_template', 'tor_example', 'guideline')),
    file_type TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(filename, category)         -- prevent duplicate ingest
);

CREATE INDEX IF NOT EXISTS idx_rag_docs_category ON rag_documents(category);
CREATE INDEX IF NOT EXISTS idx_rag_docs_ingested ON rag_documents(ingested_at);
```

### Step 2: Update `app/db/database.py`

Migration di `init_db()` sudah bersifat loop — cukup pastikan file SQL sudah ada di folder migrations. Tidak perlu ubah logic.

**Verifikasi**: cek apakah `init_db()` mem-loop semua file `.sql` di folder.:

```python
# Di database.py — pastikan ini sudah ada (dari task04 beta0.1.0):
migration_dir = Path(__file__).parent / "migrations"
for sql_file in sorted(migration_dir.glob("*.sql")):
    sql = sql_file.read_text(encoding="utf-8")
    await db.executescript(sql)
```

Jika belum, tambahkan logic tersebut agar `002_rag_documents.sql` otomatis di-run.

### Step 3: Buat `app/rag/document_tracker.py`

```python
import logging
from datetime import datetime
import aiosqlite

logger = logging.getLogger("ai-agent-hybrid.rag.tracker")


class RAGDocumentTracker:
    """Track metadata dokumen yang sudah di-ingest ke ChromaDB."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def upsert(
        self,
        doc_id: str,
        filename: str,
        category: str,
        file_type: str,
        char_count: int,
        chunk_count: int,
    ) -> None:
        """Insert atau update record dokumen."""
        now = datetime.utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO rag_documents
                    (id, filename, category, file_type, char_count, chunk_count, ingested_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filename, category) DO UPDATE SET
                    id = excluded.id,
                    file_type = excluded.file_type,
                    char_count = excluded.char_count,
                    chunk_count = excluded.chunk_count,
                    updated_at = excluded.updated_at
                """,
                (doc_id, filename, category, file_type, char_count, chunk_count, now, now)
            )
            await db.commit()
        logger.debug(f"Tracked document: {filename} [{category}] ({chunk_count} chunks)")

    async def get_all(self) -> list[dict]:
        """Ambil semua dokumen yang sudah di-ingest."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM rag_documents ORDER BY ingested_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def delete_by_filename(self, filename: str, category: str) -> None:
        """Hapus record ketika dokumen di-re-ingest atau dihapus."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM rag_documents WHERE filename = ? AND category = ?",
                (filename, category)
            )
            await db.commit()

    async def exists(self, filename: str, category: str) -> bool:
        """Cek apakah dokumen sudah pernah di-ingest."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id FROM rag_documents WHERE filename = ? AND category = ?",
                (filename, category)
            )
            row = await cursor.fetchone()
            return row is not None
```

### Step 4: Verifikasi

```python
import asyncio
import os
from app.db.database import init_db
from app.rag.document_tracker import RAGDocumentTracker

TEST_DB = "./data/test_rag_tracking.db"

async def test():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    await init_db(TEST_DB)
    tracker = RAGDocumentTracker(TEST_DB)

    # Test 1: Upsert
    await tracker.upsert(
        doc_id="abc123", filename="tor_one.md", category="tor_example",
        file_type="md", char_count=1500, chunk_count=8
    )
    assert await tracker.exists("tor_one.md", "tor_example") is True
    print("Test 1 passed: upsert & exists OK")

    # Test 2: Get all
    docs = await tracker.get_all()
    assert len(docs) == 1
    assert docs[0]["filename"] == "tor_one.md"
    assert docs[0]["chunk_count"] == 8
    print(f"Test 2 passed: get_all → {docs}")

    # Test 3: Duplicate upsert (update, bukan insert baru)
    await tracker.upsert(
        doc_id="abc123_v2", filename="tor_one.md", category="tor_example",
        file_type="md", char_count=2000, chunk_count=12
    )
    docs2 = await tracker.get_all()
    assert len(docs2) == 1  # tidak ada duplikat
    assert docs2[0]["chunk_count"] == 12  # ter-update
    print("Test 3 passed: upsert idempotent (update)")

    # Test 4: Delete
    await tracker.delete_by_filename("tor_one.md", "tor_example")
    assert await tracker.exists("tor_one.md", "tor_example") is False
    print("Test 4 passed: delete OK")

    os.remove(TEST_DB)
    print("ALL TRACKER TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Test 1 passed: upsert & exists OK
Test 2 passed: get_all → [{'id': 'abc123', 'filename': 'tor_one.md', ...}]
Test 3 passed: upsert idempotent (update)
Test 4 passed: delete OK
ALL TRACKER TESTS PASSED
```

## 7. Dependencies

- **Task 04 (beta0.1.0)** — `database.py`, `init_db()`, dan aiosqlite

## 8. Acceptance Criteria

- [ ] `002_rag_documents.sql` di-apply otomatis saat `init_db()` dipanggil
- [ ] `upsert(...)` berhasil insert record baru
- [ ] Jika filename+category sudah ada → update record, bukan insert baru (no duplicate)
- [ ] `get_all()` return list dict dengan key `filename`, `category`, `chunk_count`, `ingested_at`
- [ ] `exists("file.md", "category")` return `True` / `False`
- [ ] `delete_by_filename(...)` menghapus record

## 9. Estimasi

**Low** — ~1 jam
