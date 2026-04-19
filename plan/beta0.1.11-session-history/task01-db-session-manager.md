# Task 01: DB Migration + SessionManager Enhancement

> **Status**: [ ] Belum Dikerjakan
> **Estimasi**: Medium (1–2 jam)
> **Dependency**: Tidak ada (task pertama)

## 1. Deskripsi

Menambahkan kolom `title` ke tabel `sessions` dan membuat method `list_all()` di `SessionManager` untuk mengambil daftar session yang sudah ada. Ini adalah fondasi data untuk seluruh fitur Session History.

## 2. Tujuan Teknis

- Kolom `title` tersedia di tabel `sessions` untuk menyimpan judul session
- `SessionManager` mampu mengembalikan daftar semua session, urut dari terbaru
- Auto-title terisi dari pesan pertama user saat chat dimulai

## 3. Scope

**Yang dikerjakan:**
- File migration SQL baru
- Method `list_all()` di `SessionManager`
- Logic auto-title di `ChatService.process_message()` (saat turn pertama)

**Yang tidak dikerjakan:**
- API endpoint (task02)
- UI frontend (task04-05)

## 4. Langkah Implementasi

### 4.1 Buat Migration File

- [ ] Buat file `app/db/migrations/005_session_title.sql`:

```sql
-- Migration 005: Add title column for session history display
-- Safe to run multiple times (IF NOT EXISTS handled by column check)
-- Note: SQLite ALTER TABLE ADD COLUMN is idempotent if wrapped in try/except at app level

ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT NULL;
```

> **Catatan SQLite**: `ALTER TABLE ... ADD COLUMN` akan error jika kolom sudah ada. Karena `database.py` menggunakan `executescript()` yang tidak support `IF NOT EXISTS` untuk `ALTER TABLE`, kita perlu menangani ini. Ubah pendekatan: gunakan try/except di level Python.

- [ ] Ubah migration file agar aman:

```sql
-- Migration 005: Add title column for session history display
-- SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN
-- Error akan di-ignore oleh handler di database.py jika kolom sudah ada
ALTER TABLE sessions ADD COLUMN title TEXT DEFAULT NULL;
```

- [ ] Update `app/db/database.py` agar menangani error duplicate column:

Di fungsi `init_db()`, ganti `await db.executescript(sql)` dengan penanganan error yang lebih robust:

```python
# Saat ini (line 30-33):
for migration_file in migration_files:
    sql = migration_file.read_text(encoding="utf-8")
    await db.executescript(sql)
    logger.info(f"Migration applied: {migration_file.name}")

# Ubah menjadi:
for migration_file in migration_files:
    sql = migration_file.read_text(encoding="utf-8")
    try:
        await db.executescript(sql)
        logger.info(f"Migration applied: {migration_file.name}")
    except Exception as e:
        # ALTER TABLE ADD COLUMN gagal jika kolom sudah ada → aman di-skip
        if "duplicate column" in str(e).lower():
            logger.debug(f"Migration skipped (column exists): {migration_file.name}")
        else:
            raise
```

### 4.2 Tambah Method `list_all()` di SessionManager

- [ ] Tambahkan method berikut di `app/core/session_manager.py` (setelah method `get()`):

```python
async def list_all(self, limit: int = 50) -> list[dict]:
    """List semua session, urut dari terbaru.

    Returns:
        list[dict]: Setiap dict berisi id, title, state, turn_count,
                    created_at, updated_at, has_tor.
    """
    async with aiosqlite.connect(self.db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, title, state, turn_count,
                   created_at, updated_at,
                   CASE WHEN generated_tor IS NOT NULL THEN 1 ELSE 0 END as has_tor
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "state": row["state"],
            "turn_count": row["turn_count"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "has_tor": bool(row["has_tor"]),
        }
        for row in rows
    ]
```

### 4.3 Auto-Title dari Pesan Pertama User

- [ ] Tambahkan logic auto-title di `app/services/chat_service.py`, di method `process_message()`, **setelah blok append_message (line 111-114)** dan **sebelum update session (line 115)**:

```python
        # === Auto-title: set dari pesan pertama user ===
        if session.turn_count == 0:
            title = message[:40].strip()
            if len(message) > 40:
                title += "..."
            await self.session_mgr.update(session.id, title=title)
```

Lokasi: antara line 114 dan line 115 di `chat_service.py`.

## 5. Output yang Diharapkan

```python
# Setelah beberapa session dibuat via chat:
sessions = await session_mgr.list_all(limit=10)
# [
#   {"id": "abc-123...", "title": "Workshop Penerapan AI...", "state": "COMPLETED", "turn_count": 8, ...},
#   {"id": "def-456...", "title": "Pengadaan Server Dat...", "state": "CHATTING", "turn_count": 3, ...},
# ]
```

## 6. Acceptance Criteria

- [ ] File `app/db/migrations/005_session_title.sql` ada.
- [ ] Server bisa start tanpa error (migration berjalan).
- [ ] `SessionManager.list_all()` mengembalikan list of dict dengan key yang benar.
- [ ] Session baru yang dibuat via chat memiliki `title` terisi otomatis dari pesan pertama.
- [ ] `list_all()` mengembalikan session urut dari `updated_at DESC`.
- [ ] `has_tor` bernilai `True` untuk session yang punya `generated_tor`.
