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
