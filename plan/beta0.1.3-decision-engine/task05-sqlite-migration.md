# Task 05 — SQLite Migration: escalation_log Table

## 1. Judul Task

Buat migration SQL `004_escalation_log.sql` untuk tabel `escalation_log` (audit trail setiap eskalasi).

## 2. Deskripsi

Menambahkan tabel `escalation_log` ke SQLite untuk menyimpan detail setiap kali eskalasi terjadi: rule mana yang trigger, alasan, turn count, completeness score, dan pesan user yang memicu.

## 3. Tujuan Teknis

- Tabel `escalation_log` dengan auto-increment ID + FK ke `sessions(id)`
- Index pada `session_id` untuk query cepat
- Migration otomatis ter-apply via `init_db()` yang sudah ada

## 4. Scope

### Yang dikerjakan
- `app/db/migrations/004_escalation_log.sql`

### Yang tidak dikerjakan
- CRUD logic (itu di DecisionEngine)
- Perubahan pada `database.py` (loop migration sudah auto)

## 5. Langkah Implementasi

### Step 1: Buat `app/db/migrations/004_escalation_log.sql`

```sql
-- Migration 004: Escalation Log Table

CREATE TABLE IF NOT EXISTS escalation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rule_name TEXT NOT NULL,
    reason TEXT NOT NULL,
    turn_count INTEGER,
    completeness_score REAL,
    message_that_triggered TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_escalation_session ON escalation_log(session_id);
```

### Step 2: Verifikasi

```python
import asyncio
import os
from app.db.database import init_db

TEST_DB = "./data/test_escalation_migration.db"

async def test():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    await init_db(TEST_DB)

    import aiosqlite
    async with aiosqlite.connect(TEST_DB) as db:
        # Check escalation_log table exists
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='escalation_log'"
        )
        assert (await cursor.fetchone()) is not None, "escalation_log table missing!"

        # Check index exists
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_escalation_session'"
        )
        assert (await cursor.fetchone()) is not None, "idx_escalation_session index missing!"

    os.remove(TEST_DB)
    print("ALL MIGRATION TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
ALL MIGRATION TESTS PASSED
```

Migration 004 ter-apply otomatis bersama 001, 002, dan 003.

## 7. Dependencies

- **beta0.1.0 Task 04** — `database.py` + `init_db()` + migration loop

## 8. Acceptance Criteria

- [ ] `004_escalation_log.sql` ada di folder `app/db/migrations/`
- [ ] Tabel `escalation_log` terbuat dengan kolom: `id`, `session_id`, `triggered_at`, `rule_name`, `reason`, `turn_count`, `completeness_score`, `message_that_triggered`
- [ ] Index pada `session_id` terbuat
- [ ] `init_db()` otomatis menjalankan migration ini

## 9. Estimasi

**Low** — ~20 menit
