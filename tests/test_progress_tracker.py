"""Unit tests ProgressTracker."""
import pytest
from app.core.progress_tracker import ProgressTracker


class TestProgressTracker:
    def test_get_creates_new_state(self):
        tracker = ProgressTracker()
        state = tracker.get("session-1")
        assert state.score_history == []
        assert state.lazy_strike_count == 0

    def test_update_appends_score(self):
        tracker = ProgressTracker()
        tracker.update_after_chat("session-1", 0.33, 2)
        state = tracker.get("session-1")
        assert state.score_history == [0.33]

    def test_new_field_updates_last_turn(self):
        tracker = ProgressTracker()
        tracker.update_after_chat("session-1", 0.33, 2)
        state = tracker.get("session-1")
        assert state.last_field_filled_turn == 1
        assert state.previous_filled_count == 2

    def test_no_new_field_keeps_last_turn(self):
        tracker = ProgressTracker()
        tracker.update_after_chat("session-1", 0.33, 2)
        tracker.update_after_chat("session-1", 0.33, 2)  # same count
        state = tracker.get("session-1")
        assert state.last_field_filled_turn == 1  # unchanged

    def test_reset_clears_state(self):
        tracker = ProgressTracker()
        tracker.update_after_chat("session-1", 0.5, 3)
        tracker.reset("session-1")
        state = tracker.get("session-1")
        assert state.score_history == []

    def test_multiple_sessions_independent(self):
        tracker = ProgressTracker()
        tracker.update_after_chat("s1", 0.2, 1)
        tracker.update_after_chat("s2", 0.5, 3)
        assert tracker.get("s1").score_history == [0.2]
        assert tracker.get("s2").score_history == [0.5]
