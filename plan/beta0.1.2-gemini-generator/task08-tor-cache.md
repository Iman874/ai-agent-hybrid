# Task 08 — TORCache: SQLite Cache Layer

## 1. Judul Task

Implementasikan `TORCache` — layer cache SQLite untuk menyimpan dan mengambil TOR yang sudah di-generate, menghindari pemanggilan Gemini berulang.

## 2. Deskripsi

Setiap kali TOR berhasil di-generate, simpan ke tabel `tor_cache`. Pada request generate berikutnya untuk session yang sama, serve dari cache (jika `force_regenerate=False`).

## 3. Tujuan Teknis

- `get(session_id) → TORDocument | None` — ambil dari cache
- `store(session_id, tor_doc)` — simpan/replace ke cache (INSERT OR REPLACE)
- Menggunakan model `TORDocument` dan `TORMetadata` dari Task 01

## 4. Scope

### Yang dikerjakan
- `app/db/repositories/cache_repo.py` — class `TORCache`
- `app/db/repositories/__init__.py`

### Yang tidak dikerjakan
- Cache invalidation strategy (simple: overwrite)
- Eviction/TTL

## 5. Langkah Implementasi

### Step 1: Buat `app/db/repositories/__init__.py`

```python
"""Database repository layer."""
```

### Step 2: Buat `app/db/repositories/cache_repo.py`

```python
import logging
import aiosqlite
from app.models.generate import TORDocument, TORMetadata

logger = logging.getLogger("ai-agent-hybrid.cache")


class TORCache:
    """Cache layer untuk TOR documents di SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def get(self, session_id: str) -> TORDocument | None:
        """Ambil TOR dari cache. Return None jika tidak ada."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tor_cache WHERE session_id = ?", (session_id,)
            )
            row = await cursor.fetchone()
            if row:
                logger.debug(f"Cache hit for session {session_id}")
                return TORDocument(
                    content=row["tor_content"],
                    metadata=TORMetadata(
                        generated_by=row["model_used"],
                        mode=row["mode"],
                        word_count=row["word_count"] or 0,
                        generation_time_ms=row["generation_time_ms"] or 0,
                        prompt_tokens=row["prompt_tokens"] or 0,
                        completion_tokens=row["completion_tokens"] or 0,
                    )
                )
            logger.debug(f"Cache miss for session {session_id}")
            return None

    async def store(self, session_id: str, tor: TORDocument) -> None:
        """Simpan TOR ke cache. Overwrite jika sudah ada."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO tor_cache "
                "(session_id, tor_content, model_used, mode, word_count, "
                "generation_time_ms, prompt_tokens, completion_tokens) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, tor.content, tor.metadata.generated_by,
                 tor.metadata.mode, tor.metadata.word_count,
                 tor.metadata.generation_time_ms, tor.metadata.prompt_tokens,
                 tor.metadata.completion_tokens)
            )
            await db.commit()
        logger.debug(f"Cached TOR for session {session_id}")
```

### Step 3: Verifikasi

```python
import asyncio, os
from app.db.database import init_db
from app.db.repositories.cache_repo import TORCache
from app.models.generate import TORDocument, TORMetadata

TEST_DB = "./data/test_cache.db"

async def test():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    await init_db(TEST_DB)

    cache = TORCache(TEST_DB)

    # Test 1: Cache miss
    result = await cache.get("nonexistent")
    assert result is None
    print("Test 1: cache miss OK")

    # Test 2: Store and get
    tor = TORDocument(
        content="# TOR Test\n\nIni TOR.",
        metadata=TORMetadata(
            generated_by="gemini-2.0-flash", mode="standard",
            word_count=5, generation_time_ms=1000
        )
    )
    await cache.store("session-123", tor)
    cached = await cache.get("session-123")
    assert cached is not None
    assert cached.content == "# TOR Test\n\nIni TOR."
    assert cached.metadata.mode == "standard"
    print("Test 2: store & get OK")

    # Test 3: Overwrite
    tor2 = TORDocument(
        content="# TOR Updated",
        metadata=TORMetadata(
            generated_by="gemini-2.0-flash", mode="standard",
            word_count=3, generation_time_ms=500
        )
    )
    await cache.store("session-123", tor2)
    cached2 = await cache.get("session-123")
    assert cached2.content == "# TOR Updated"
    print("Test 3: overwrite OK")

    os.remove(TEST_DB)
    print("ALL CACHE TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Test 1: cache miss OK
Test 2: store & get OK
Test 3: overwrite OK
ALL CACHE TESTS PASSED
```

## 7. Dependencies

- **Task 01** — `TORDocument`, `TORMetadata` models
- **Task 03** — `tor_cache` table via migration

## 8. Acceptance Criteria

- [ ] `get()` return `TORDocument` jika ada, `None` jika kosong
- [ ] `store()` insert baru atau replace existing
- [ ] Data ter-persist di SQLite (survive restart)
- [ ] Semua field metadata ter-simpan dan ter-restore dengan benar

## 9. Estimasi

**Low** — ~1 jam
