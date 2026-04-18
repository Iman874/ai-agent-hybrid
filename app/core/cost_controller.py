import logging
from datetime import datetime, timedelta
import aiosqlite

from app.core.session_manager import SessionManager
from app.config import Settings
from app.utils.errors import RateLimitError

logger = logging.getLogger("ai-agent-hybrid.cost")


class CostController:
    """Rate limiting dan cost tracking untuk Gemini API calls."""

    def __init__(self, session_mgr: SessionManager, settings: Settings):
        self.session_mgr = session_mgr
        self.db_path = session_mgr.db_path
        self.max_per_session = settings.max_gemini_calls_per_session
        self.max_per_hour = settings.max_gemini_calls_per_hour

    async def check(self, session_id: str) -> None:
        """Raise RateLimitError jika melebihi batas."""
        # Check per-session limit
        session = await self.session_mgr.get(session_id)
        if session.gemini_calls_count >= self.max_per_session:
            raise RateLimitError(
                f"Batas {self.max_per_session} panggilan Gemini per session tercapai.",
                details=f"session_id: {session_id}, calls: {session.gemini_calls_count}"
            )

        # Check global hourly limit
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM gemini_call_log WHERE called_at > ? AND success = TRUE",
                (one_hour_ago.isoformat(),)
            )
            row = await cursor.fetchone()
            hourly_count = row[0]

        if hourly_count >= self.max_per_hour:
            raise RateLimitError(
                f"Batas {self.max_per_hour} panggilan Gemini per jam tercapai. "
                "Coba lagi dalam beberapa menit.",
                details=f"hourly_count: {hourly_count}"
            )

        logger.debug(
            f"Cost check passed: session={session.gemini_calls_count}/{self.max_per_session}, "
            f"hourly={hourly_count}/{self.max_per_hour}"
        )

    async def log_call(
        self, session_id: str, model: str, mode: str,
        prompt_tokens: int, completion_tokens: int,
        duration_ms: int, success: bool, error_msg: str | None = None
    ) -> None:
        """Log setiap panggilan Gemini untuk tracking."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO gemini_call_log "
                "(session_id, model, mode, prompt_tokens, completion_tokens, "
                "duration_ms, success, error_message) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, model, mode, prompt_tokens, completion_tokens,
                 duration_ms, success, error_msg)
            )
            await db.commit()
        logger.debug(
            f"Logged Gemini call: session={session_id}, model={model}, "
            f"success={success}, tokens={prompt_tokens}+{completion_tokens}"
        )
