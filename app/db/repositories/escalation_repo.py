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
