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
