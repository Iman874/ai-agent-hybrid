import logging
from app.models.escalation import ProgressState

logger = logging.getLogger("ai-agent-hybrid.progress")


class ProgressTracker:
    """Track completeness progress per session (in-memory)."""

    def __init__(self):
        self._states: dict[str, ProgressState] = {}

    def get(self, session_id: str) -> ProgressState:
        """Ambil state, buat baru jika belum ada."""
        if session_id not in self._states:
            self._states[session_id] = ProgressState()
        return self._states[session_id]

    def update_after_chat(
        self,
        session_id: str,
        new_completeness: float,
        new_filled_count: int,
    ):
        """Update progress setelah chat turn selesai."""
        state = self.get(session_id)
        state.score_history.append(new_completeness)

        # Cek apakah ada field baru terisi
        if new_filled_count > state.previous_filled_count:
            current_turn = len(state.score_history)
            state.last_field_filled_turn = current_turn
            state.previous_filled_count = new_filled_count

    def reset(self, session_id: str):
        """Reset progress state (misal saat session di-reset)."""
        self._states.pop(session_id, None)
