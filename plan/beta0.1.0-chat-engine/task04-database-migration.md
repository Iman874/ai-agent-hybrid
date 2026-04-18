# Task 04 — Database Setup & Migration

## 1. Judul Task

Setup SQLite database, buat migration script, dan implementasi `init_db()` function.

## 2. Deskripsi

Membuat sistem database: file migration SQL untuk tabel `sessions` dan `chat_messages`, serta function untuk inisialisasi database saat aplikasi startup. Menggunakan `aiosqlite` untuk async operations.

## 3. Tujuan Teknis

- File migration SQL terbuat dan bisa di-execute
- Function `init_db()` bisa auto-create tabel jika belum ada
- Folder `data/` auto-created jika belum exist
- SQLite WAL mode aktif untuk concurrent access

## 4. Scope

### Yang dikerjakan
- `app/db/migrations/001_initial.sql` — DDL statements
- `app/db/database.py` — `init_db()` dan helper functions
- Auto-create `data/` directory

### Yang tidak dikerjakan
- CRUD queries (itu di task SessionManager)
- FastAPI lifespan integration (itu di task FastAPI app)

## 5. Langkah Implementasi

### Step 1: Buat `app/db/migrations/001_initial.sql`

```sql
-- Migration 001: Initial schema for sessions and chat messages
-- Dijalankan otomatis saat application startup

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state TEXT DEFAULT 'NEW' CHECK(state IN ('NEW','CHATTING','READY','ESCALATED','GENERATING','COMPLETED')),
    turn_count INTEGER DEFAULT 0,
    completeness_score REAL DEFAULT 0.0,
    extracted_data_json TEXT DEFAULT '{}',
    generated_tor TEXT,
    escalation_reason TEXT,
    gemini_calls_count INTEGER DEFAULT 0,
    total_tokens_local INTEGER DEFAULT 0,
    total_tokens_gemini INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content TEXT NOT NULL,
    parsed_status TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_state ON sessions(state);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
```

### Step 2: Buat `app/db/database.py`

```python
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger("ai-agent-hybrid.db")

MIGRATION_DIR = Path(__file__).parent / "migrations"


async def init_db(db_path: str) -> None:
    """
    Inisialisasi database:
    1. Buat folder parent jika belum ada
    2. Connect ke SQLite
    3. Aktifkan WAL mode
    4. Jalankan semua file migration
    """
    # Auto-create parent directory
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode untuk concurrent access
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("PRAGMA busy_timeout=5000")

        # Run semua migration files secara berurutan
        migration_files = sorted(MIGRATION_DIR.glob("*.sql"))
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            await db.executescript(sql)
            logger.info(f"Migration applied: {migration_file.name}")

        await db.commit()
        logger.info(f"Database initialized at: {db_path}")


async def get_db_connection(db_path: str) -> aiosqlite.Connection:
    """Get a database connection (caller harus close sendiri)."""
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    return db
```

### Step 3: Buat `app/db/__init__.py`

```python
from app.db.database import init_db, get_db_connection
```

### Step 4: Test manual

```python
import asyncio
from app.db.database import init_db

async def test():
    await init_db("./data/sessions.db")
    print("DB initialized!")

asyncio.run(test())
```

Verifikasi: file `data/sessions.db` terbuat, dan tabel `sessions` + `chat_messages` ada.

## 6. Output yang Diharapkan

File yang dibuat:
- `app/db/migrations/001_initial.sql` — 2 tabel, 3 index
- `app/db/database.py` — `init_db()`, `get_db_connection()`

Behavior setelah `init_db("./data/sessions.db")`:

```
data/
└── sessions.db    ← file SQLite terbuat

Tables:
├── sessions       ← 12 kolom
└── chat_messages  ← 6 kolom + 1 index
```

## 7. Dependencies

- **Task 01** — `aiosqlite` sudah terinstall

## 8. Acceptance Criteria

- [ ] `app/db/migrations/001_initial.sql` berisi CREATE TABLE yang valid
- [ ] `init_db()` auto-create folder `data/` jika belum ada
- [ ] `init_db()` berhasil tanpa error jika dipanggil pertama kali
- [ ] `init_db()` berhasil tanpa error jika dipanggil KEDUA kali (idempotent, pakai `IF NOT EXISTS`)
- [ ] Tabel `sessions` punya 12 kolom sesuai spec
- [ ] Tabel `chat_messages` punya 6 kolom sesuai spec
- [ ] Index `idx_messages_session` terbuat
- [ ] Foreign key `chat_messages.session_id → sessions.id` aktif
- [ ] WAL mode aktif (cek `PRAGMA journal_mode` = `wal`)
- [ ] `get_db_connection()` return connection dengan row_factory = Row

## 9. Estimasi

**Low** — ~45 menit
