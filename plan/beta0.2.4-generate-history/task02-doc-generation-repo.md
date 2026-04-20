# Task 2: Repository — `DocGenerationRepo` CRUD

## 1. Judul Task
Buat Python repository class untuk operasi CRUD pada tabel `document_generations`.

## 2. Deskripsi
Repository ini menjadi satu-satunya interface antara business logic dan tabel `document_generations`. Semua operasi database (create, read, update status, list, delete) dilakukan melalui class ini.

## 3. Tujuan Teknis
- Class `DocGenerationRepo` di `app/db/repositories/doc_generation_repo.py`
- Method: `create`, `update_completed`, `update_failed`, `list_all`, `get`, `delete`
- Menggunakan `aiosqlite` (sama seperti pattern yang ada)
- Export di `__init__.py`

## 4. Scope
### Yang dikerjakan
- Buat file `app/db/repositories/doc_generation_repo.py`
- Update `app/db/repositories/__init__.py` untuk export

### Yang tidak dikerjakan
- Tidak membuat API endpoints (task 4-5)
- Tidak mengubah Pydantic models (task 3)

## 5. Langkah Implementasi

### Step 1: Buat `app/db/repositories/doc_generation_repo.py`

```python
import json
import logging
import aiosqlite

logger = logging.getLogger("ai-agent-hybrid.doc_generation")


class DocGenerationRepo:
    """Repository untuk tabel document_generations."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create(
        self,
        gen_id: str,
        filename: str,
        file_size: int,
        context: str,
        style_id: str | None,
        style_name: str | None,
    ) -> None:
        """Insert record baru dengan status 'processing'."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO document_generations
                   (id, filename, file_size, context, style_id, style_name, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'processing')""",
                (gen_id, filename, file_size, context, style_id, style_name),
            )
            await db.commit()
        logger.info(f"DocGeneration created: {gen_id}, file={filename}")

    async def update_completed(
        self, gen_id: str, tor_content: str, metadata_json: str
    ) -> None:
        """Update status menjadi 'completed' dengan tor_content dan metadata."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE document_generations
                   SET status='completed', tor_content=?, metadata_json=?
                   WHERE id=?""",
                (tor_content, metadata_json, gen_id),
            )
            await db.commit()
        logger.info(f"DocGeneration completed: {gen_id}")

    async def update_failed(self, gen_id: str, error_message: str) -> None:
        """Update status menjadi 'failed' dengan error message."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE document_generations
                   SET status='failed', error_message=?
                   WHERE id=?""",
                (error_message, gen_id),
            )
            await db.commit()
        logger.warning(f"DocGeneration failed: {gen_id}, error={error_message[:100]}")

    async def list_all(self, limit: int = 30) -> list[dict]:
        """List semua records, urut terbaru."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, filename, file_size, style_name, status,
                          metadata_json, created_at
                   FROM document_generations
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            )
            rows = await cursor.fetchall()

        results = []
        for row in rows:
            meta = {}
            try:
                meta = json.loads(row["metadata_json"] or "{}")
            except json.JSONDecodeError:
                pass
            results.append({
                "id": row["id"],
                "filename": row["filename"],
                "file_size": row["file_size"],
                "style_name": row["style_name"],
                "status": row["status"],
                "word_count": meta.get("word_count"),
                "created_at": row["created_at"],
            })
        return results

    async def get(self, gen_id: str) -> dict | None:
        """Get detail satu record by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM document_generations WHERE id=?", (gen_id,)
            )
            row = await cursor.fetchone()

        if not row:
            return None

        meta = None
        try:
            raw = json.loads(row["metadata_json"] or "{}")
            if raw:
                meta = raw
        except json.JSONDecodeError:
            pass

        return {
            "id": row["id"],
            "filename": row["filename"],
            "file_size": row["file_size"],
            "context": row["context"],
            "style_id": row["style_id"],
            "style_name": row["style_name"],
            "status": row["status"],
            "tor_content": row["tor_content"],
            "metadata": meta,
            "error_message": row["error_message"],
            "created_at": row["created_at"],
        }

    async def delete(self, gen_id: str) -> bool:
        """Hapus record. Return True jika berhasil."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM document_generations WHERE id=?", (gen_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
```

### Step 2: Update `app/db/repositories/__init__.py`

Tambahkan:
```python
from .doc_generation_repo import DocGenerationRepo
```

## 6. Output yang Diharapkan

```python
repo = DocGenerationRepo("data/app.db")
await repo.create("doc-abc123", "TOR.docx", 43000, "konteks", None, "Standar")
await repo.update_completed("doc-abc123", "# TOR Content", '{"word_count": 500}')
items = await repo.list_all()
# [{"id": "doc-abc123", "filename": "TOR.docx", "status": "completed", ...}]
```

## 7. Dependencies
- Task 1 (tabel harus sudah ada)

## 8. Acceptance Criteria
- [ ] File `doc_generation_repo.py` ada di `app/db/repositories/`
- [ ] Class memiliki 6 method: `create`, `update_completed`, `update_failed`, `list_all`, `get`, `delete`
- [ ] Semua method menggunakan `async with aiosqlite.connect()`
- [ ] Exported dari `__init__.py`
- [ ] Menggunakan `logging` (bukan `print`)

## 9. Estimasi
**Medium** (~1 jam)
