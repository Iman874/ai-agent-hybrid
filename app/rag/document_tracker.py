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
