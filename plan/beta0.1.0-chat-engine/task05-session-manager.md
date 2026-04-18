# Task 05 — Session Manager (CRUD Operations)

## 1. Judul Task

Implementasi `SessionManager` class — CRUD session dan chat messages di SQLite.

## 2. Deskripsi

Membuat class `SessionManager` yang menangani semua operasi database untuk sessions dan chat messages: create session baru, get session by ID, update session fields, append chat messages, dan get chat history.

## 3. Tujuan Teknis

- `SessionManager` bisa create session baru dengan UUID
- `SessionManager` bisa get session by ID (atau raise `SessionNotFoundError`)
- `SessionManager` bisa update field session (state, turn_count, extracted_data, dll)
- `SessionManager` bisa append message ke chat history
- `SessionManager` bisa get chat history untuk satu session
- Konversi row SQLite ↔ Pydantic model bekerja dengan benar

## 4. Scope

### Yang dikerjakan
- `app/core/session_manager.py` — class lengkap
- CRUD: create, get, update, append_message, get_chat_history
- Helper: `_row_to_session()` untuk konversi SQLite row → Pydantic Session

### Yang tidak dikerjakan
- Session cleanup/expiry (nanti)
- REST endpoint (itu di task berbeda)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/session_manager.py`

```python
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
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    def _row_to_session(self, row: dict) -> Session:
        """Convert SQLite row dict → Pydantic Session model."""
        extracted_json = row.get("extracted_data_json", "{}")
        try:
            extracted = TORData(**json.loads(extracted_json))
        except (json.JSONDecodeError, Exception):
            extracted = TORData()

        return Session(
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
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
```

### Step 2: Test manual

```python
import asyncio
from app.db.database import init_db
from app.core.session_manager import SessionManager

async def test():
    db_path = "./data/test_sessions.db"
    await init_db(db_path)
    mgr = SessionManager(db_path)

    # Create
    session = await mgr.create()
    print(f"Created: {session.id}, state={session.state}")

    # Get
    fetched = await mgr.get(session.id)
    print(f"Fetched: {fetched.id}, state={fetched.state}")

    # Append messages
    await mgr.append_message(session.id, "user", "Halo, saya mau buat TOR")
    await mgr.append_message(session.id, "assistant", "Baik, tentang apa?", "NEED_MORE_INFO")

    # Get history
    history = await mgr.get_chat_history(session.id)
    print(f"History: {len(history)} messages")

    # Update
    from app.models.tor import TORData
    data = TORData(judul="Workshop AI")
    await mgr.update(session.id, state="CHATTING", turn_count=1, extracted_data=data)
    updated = await mgr.get(session.id)
    print(f"Updated: state={updated.state}, data.judul={updated.extracted_data.judul}")

    # Not found
    try:
        await mgr.get("non-existent-id")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Created: 550e8400-..., state=NEW
Fetched: 550e8400-..., state=NEW
History: 2 messages
Updated: state=CHATTING, data.judul=Workshop AI
Error: Session tidak ditemukan. Mulai percakapan baru.
```

## 7. Dependencies

- **Task 01** — aiosqlite terinstall
- **Task 02** — `SessionNotFoundError` terdefinisi
- **Task 03** — Pydantic models `Session`, `ChatMessage`, `TORData`
- **Task 04** — Database sudah bisa di-init

## 8. Acceptance Criteria

- [ ] `SessionManager.create()` menghasilkan session dengan UUID valid dan state `NEW`
- [ ] `SessionManager.get(valid_id)` return Session object yang lengkap
- [ ] `SessionManager.get(invalid_id)` raise `SessionNotFoundError`
- [ ] `SessionManager.update()` bisa update satu atau lebih field sekaligus
- [ ] `SessionManager.update(extracted_data=TORData(...))` menyimpan sebagai JSON string
- [ ] `SessionManager.get()` bisa baca kembali `extracted_data_json` menjadi `TORData`
- [ ] `SessionManager.append_message()` berhasil insert ke `chat_messages`
- [ ] `SessionManager.get_chat_history()` return messages urut timestamp ASC
- [ ] `updated_at` otomatis di-update setiap kali `update()` dipanggil

## 9. Estimasi

**Medium** — ~2 jam
