# Task 03 — SQLite Migration: tor_cache & gemini_call_log Tables

## 1. Judul Task

Buat migration SQL `003_gemini_tables.sql` untuk tabel `tor_cache` (cache dokumen TOR) dan `gemini_call_log` (tracking API call).

## 2. Deskripsi

Menambahkan dua tabel baru ke SQLite: `tor_cache` untuk menyimpan TOR yang sudah di-generate agar tidak perlu re-call Gemini, dan `gemini_call_log` untuk tracking semua panggilan Gemini (cost control & auditing).

## 3. Tujuan Teknis

- Tabel `tor_cache` dengan `session_id` sebagai PK + FK ke `sessions(id)`
- Tabel `gemini_call_log` dengan auto-increment ID + index waktu
- Migration otomatis ter-apply via `init_db()` yang sudah ada

## 4. Scope

### Yang dikerjakan
- `app/db/migrations/003_gemini_tables.sql`

### Yang tidak dikerjakan
- CRUD logic (itu task terpisah)
- Perubahan pada `database.py` (loop migration sudah auto)

## 5. Langkah Implementasi

### Step 1: Buat `app/db/migrations/003_gemini_tables.sql`

```sql
-- Migration 003: Gemini Generator Tables

-- Cache TOR yang sudah di-generate
CREATE TABLE IF NOT EXISTS tor_cache (
    session_id TEXT PRIMARY KEY,
    tor_content TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT NOT NULL,
    mode TEXT NOT NULL                CHECK(mode IN ('standard', 'escalation')),
    word_count INTEGER,
    generation_time_ms INTEGER,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Log setiap panggilan ke Gemini API (cost tracking)
CREATE TABLE IF NOT EXISTS gemini_call_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model TEXT NOT NULL,
    mode TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    duration_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_gemini_calls_time ON gemini_call_log(called_at);
CREATE INDEX IF NOT EXISTS idx_gemini_calls_session ON gemini_call_log(session_id);
```

### Step 2: Verifikasi

```python
import asyncio
import os
from app.db.database import init_db

TEST_DB = "./data/test_gemini_migration.db"

async def test():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    await init_db(TEST_DB)

    import aiosqlite
    async with aiosqlite.connect(TEST_DB) as db:
        # Check tor_cache table exists
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tor_cache'"
        )
        assert (await cursor.fetchone()) is not None, "tor_cache table missing!"

        # Check gemini_call_log table exists
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='gemini_call_log'"
        )
        assert (await cursor.fetchone()) is not None, "gemini_call_log table missing!"

    os.remove(TEST_DB)
    print("ALL MIGRATION TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
ALL MIGRATION TESTS PASSED
```

Migration 003 ter-apply otomatis bersama 001 dan 002.

## 7. Dependencies

- **Task 04 (beta0.1.0)** — `database.py` + `init_db()` + migration loop

## 8. Acceptance Criteria

- [ ] `003_gemini_tables.sql` ada di folder `app/db/migrations/`
- [ ] Tabel `tor_cache` terbuat dengan kolom: `session_id`, `tor_content`, `generated_at`, `model_used`, `mode`, `word_count`, `generation_time_ms`, `prompt_tokens`, `completion_tokens`
- [ ] Tabel `gemini_call_log` terbuat dengan kolom: `id`, `session_id`, `called_at`, `model`, `mode`, `prompt_tokens`, `completion_tokens`, `duration_ms`, `success`, `error_message`
- [ ] Index pada `called_at` dan `session_id` terbuat
- [ ] `init_db()` otomatis menjalankan migration ini

## 9. Estimasi

**Low** — ~30 menit
