# Task 06 — EscalationLogger: Audit Trail ke SQLite

## 1. Judul Task

Implementasikan `EscalationLogger` — class async untuk menyimpan log eskalasi ke tabel `escalation_log` dan query history eskalasi per session.

## 2. Deskripsi

Setiap kali eskalasi terjadi (baik dari pre-routing check maupun LLM decision), DetailPersistenceLogger mencatat alasan, rule, turn count, dan pesan pemicu ke SQLite. Berguna untuk auditing dan debugging.

## 3. Tujuan Teknis

- `log(session_id, decision, turn_count, score, message)` — insert record
- `get_history(session_id) → list[dict]` — ambil log eskalasi per session

## 4. Scope

### Yang dikerjakan
- `app/db/repositories/escalation_repo.py` — class `EscalationLogger`

### Yang tidak dikerjakan
- Analytics/dashboard
- Retention policy

## 5. Langkah Implementasi

### Step 1: Buat `app/db/repositories/escalation_repo.py`

```python
import logging
import aiosqlite
from app.models.escalation import EscalationDecision

logger = logging.getLogger("ai-agent-hybrid.escalation.log")


class EscalationLogger:
    """Log setiap eskalasi ke SQLite untuk audit trail."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def log(
        self,
        session_id: str,
        decision: EscalationDecision,
        turn_count: int,
        completeness_score: float,
        triggering_message: str,
    ) -> None:
        """Insert escalation record ke database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO escalation_log "
                "(session_id, rule_name, reason, turn_count, "
                "completeness_score, message_that_triggered) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, decision.rule_name, decision.reason,
                 turn_count, completeness_score,
                 triggering_message[:500])
            )
            await db.commit()
        logger.info(
            f"Escalation logged: session={session_id}, "
            f"rule={decision.rule_name}, turn={turn_count}"
        )

    async def get_history(self, session_id: str) -> list[dict]:
        """Ambil semua log eskalasi untuk satu session."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM escalation_log WHERE session_id = ? "
                "ORDER BY triggered_at ASC",
                (session_id,)
            )
            rows = await cursor.fetchall()
        return [dict(row) for row in rows]
```

### Step 2: Verifikasi

```python
import asyncio, os
from app.db.database import init_db
from app.db.repositories.escalation_repo import EscalationLogger
from app.models.escalation import EscalationDecision

TEST_DB = "./data/test_escalation_log.db"

async def test():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    await init_db(TEST_DB)

    repo = EscalationLogger(TEST_DB)

    # Test 1: Log escalation
    decision = EscalationDecision(
        should_escalate=True,
        rule_name="lazy_pattern",
        reason="User menunjukkan pola tidak kooperatif",
        confidence=0.9,
    )
    # Need session in DB first
    import aiosqlite
    async with aiosqlite.connect(TEST_DB) as db:
        await db.execute(
            "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
            ("test-session", "2026-01-01", "2026-01-01")
        )
        await db.commit()

    await repo.log("test-session", decision, 5, 0.33, "terserah aja")
    print("Test 1: log escalation OK")

    # Test 2: Get history
    history = await repo.get_history("test-session")
    assert len(history) == 1
    assert history[0]["rule_name"] == "lazy_pattern"
    assert history[0]["turn_count"] == 5
    print("Test 2: get history OK")

    # Test 3: Empty history
    empty = await repo.get_history("nonexistent")
    assert len(empty) == 0
    print("Test 3: empty history OK")

    os.remove(TEST_DB)
    print("ALL ESCALATION LOGGER TESTS PASSED")

asyncio.run(test())
```

## 6. Output yang Diharapkan

Escalation events ter-persist di SQLite dan bisa di-query per session.

## 7. Dependencies

- **Task 01** — `EscalationDecision` model
- **Task 05** — `escalation_log` table via migration

## 8. Acceptance Criteria

- [ ] `log()` insert record ke `escalation_log`
- [ ] `log()` truncate message ke maks 500 chars
- [ ] `get_history()` return list of dicts ordered by timestamp
- [ ] Empty session returns empty list

## 9. Estimasi

**Low** — ~45 menit
