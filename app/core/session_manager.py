import uuid
import json
import logging
from datetime import datetime

import aiosqlite

from app.models.session import Session, ChatMessage
from app.models.tor import TORData
from app.utils.errors import SessionNotFoundError

logger = logging.getLogger("ai-agent-hybrid.session")


class SessionManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create(self) -> Session:
        """Buat session baru dengan UUID v4."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
                (session_id, now.isoformat(), now.isoformat()),
            )
            await db.commit()

        logger.info(f"Session created: {session_id}")
        return Session(
            id=session_id,
            created_at=now,
            updated_at=now,
            state="NEW",
        )

    async def get(self, session_id: str) -> Session:
        """Get session by ID. Raise SessionNotFoundError jika tidak ada."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            )
            row = await cursor.fetchone()

        if not row:
            raise SessionNotFoundError(session_id)

        return self._row_to_session(dict(row))

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

    async def update(self, session_id: str, **kwargs) -> None:
        """
        Update satu atau lebih field di session.
        Contoh: await session_mgr.update(sid, state="CHATTING", turn_count=2)

        Field khusus:
        - extracted_data: TORData → disimpan sebagai JSON string di kolom extracted_data_json
        """
        set_clauses = []
        values = []

        for key, value in kwargs.items():
            if key == "extracted_data":
                set_clauses.append("extracted_data_json = ?")
                if hasattr(value, "model_dump_json"):
                    values.append(value.model_dump_json())
                else:
                    values.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = ?")
                values.append(value)

        # Selalu update timestamp
        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())

        # WHERE clause
        values.append(session_id)

        query = f"UPDATE sessions SET {', '.join(set_clauses)} WHERE id = ?"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, values)
            await db.commit()

        logger.debug(f"Session updated: {session_id}, fields: {list(kwargs.keys())}")

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        parsed_status: str | None = None,
    ) -> None:
        """Tambah satu pesan ke chat history."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO chat_messages (session_id, role, content, parsed_status) "
                "VALUES (?, ?, ?, ?)",
                (session_id, role, content, parsed_status),
            )
            await db.commit()

    async def get_chat_history(self, session_id: str) -> list[ChatMessage]:
        """Ambil semua chat messages untuk satu session, urut timestamp ASC."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            )
            rows = await cursor.fetchall()

        return [
            ChatMessage(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                parsed_status=row["parsed_status"],
                timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"],
            )
            for row in rows
        ]

    async def delete_session(self, session_id: str) -> bool:
        """Hapus session beserta semua data terkait."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "DELETE FROM chat_messages WHERE session_id = ?",
                    (session_id,),
                )
                cursor = await db.execute(
                    "DELETE FROM sessions WHERE id = ?",
                    (session_id,),
                )
                await db.commit()
                return cursor.rowcount > 0
            except Exception as exc:
                logger.error("Gagal hapus sesi %s: %s", session_id, exc)
                return False

    def _row_to_session(self, row: dict) -> Session:
        """Convert SQLite row dict → Pydantic Session model."""
        extracted_json = row.get("extracted_data_json", "{}")
        try:
            extracted = TORData(**json.loads(extracted_json))
        except (json.JSONDecodeError, Exception):
            extracted = TORData()

        return Session(
            id=row["id"],
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"],
            state=row["state"],
            turn_count=row["turn_count"],
            completeness_score=row["completeness_score"],
            extracted_data=extracted,
            generated_tor=row["generated_tor"],
            escalation_reason=row["escalation_reason"],
            gemini_calls_count=row["gemini_calls_count"],
            total_tokens_local=row["total_tokens_local"],
            total_tokens_gemini=row["total_tokens_gemini"],
        )
