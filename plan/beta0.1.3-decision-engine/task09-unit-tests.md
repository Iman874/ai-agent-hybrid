# Task 09 — Unit Tests: EscalationChecker & ProgressTracker

## 1. Judul Task

Buat unit tests komprehensif untuk `EscalationChecker` (semua 5 rules + edge cases) dan `ProgressTracker` (stagnation detection, field tracking).

## 2. Deskripsi

Unit tests yang tidak membutuhkan service external (Ollama/Gemini/SQLite). Menggunakan dummy Session dan ProgressState untuk menguji setiap rule escalation secara terisolasi, serta ProgressTracker state management.

## 3. Tujuan Teknis

- `tests/test_escalation_checker.py` — 10+ tests untuk semua 5 rules
- `tests/test_progress_tracker.py` — 5+ tests untuk tracking logic

## 4. Scope

### Yang dikerjakan
- `tests/test_escalation_checker.py`
- `tests/test_progress_tracker.py`

### Yang tidak dikerjakan
- Integration tests (itu task 10)
- DecisionEngine tests (itu task 10)

## 5. Langkah Implementasi

### Step 1: Buat `tests/test_escalation_checker.py`

```python
"""Unit tests EscalationChecker — semua 5 rules."""
import pytest
from datetime import datetime
from app.core.escalation_checker import EscalationChecker
from app.core.escalation_config import EscalationConfig
from app.models.escalation import ProgressState
from app.models.session import Session


@pytest.fixture
def checker():
    return EscalationChecker(EscalationConfig())


def make_session(**kwargs):
    now = datetime.utcnow()
    defaults = dict(id="test", created_at=now, updated_at=now, state="CHATTING", turn_count=3)
    defaults.update(kwargs)
    return Session(**defaults)


class TestAbsoluteMaxTurns:
    def test_at_max_turns_triggers(self, checker):
        session = make_session(turn_count=10)
        progress = ProgressState()
        result = checker.check_pre_routing("halo", session, progress)
        assert result.should_escalate is True
        assert result.rule_name == "absolute_max_turns"

    def test_below_max_turns_passes(self, checker):
        session = make_session(turn_count=9)
        progress = ProgressState()
        result = checker.check_pre_routing("halo", session, progress)
        assert result.should_escalate is False


class TestLazyPattern:
    def test_first_lazy_tolerated(self, checker):
        session = make_session()
        progress = ProgressState()
        result = checker.check_pre_routing("terserah aja", session, progress)
        assert result.should_escalate is False
        assert progress.lazy_strike_count == 1

    def test_second_lazy_triggers(self, checker):
        session = make_session()
        progress = ProgressState(lazy_strike_count=1)
        result = checker.check_pre_routing("gak tau", session, progress)
        assert result.should_escalate is True
        assert result.rule_name == "lazy_pattern"

    def test_non_lazy_message(self, checker):
        session = make_session()
        progress = ProgressState()
        result = checker.check_pre_routing("Timeline nya 3 hari di bulan Juli", session, progress)
        assert result.should_escalate is False
        assert progress.lazy_strike_count == 0

    def test_case_insensitive_lazy(self, checker):
        session = make_session()
        progress = ProgressState()
        result = checker.check_pre_routing("TERSERAH AJA", session, progress)
        assert result.should_escalate is False  # first time tolerated
        assert progress.lazy_strike_count == 1


class TestShortInput:
    def test_short_input_consecutive_triggers(self, checker):
        session = make_session(turn_count=3)
        progress = ProgressState(short_input_streak=1)
        result = checker.check_pre_routing("ok", session, progress)
        assert result.should_escalate is True
        assert result.rule_name == "short_input_consecutive"

    def test_short_input_first_time_tolerated(self, checker):
        session = make_session(turn_count=3)
        progress = ProgressState(short_input_streak=0)
        result = checker.check_pre_routing("ok", session, progress)
        assert result.should_escalate is False
        assert progress.short_input_streak == 1

    def test_long_input_resets_streak(self, checker):
        session = make_session(turn_count=3)
        progress = ProgressState(short_input_streak=1)
        result = checker.check_pre_routing("Timeline nya Juli 2026 selama 3 hari", session, progress)
        assert result.should_escalate is False
        assert progress.short_input_streak == 0


class TestStagnation:
    def test_stagnation_triggers(self, checker):
        session = make_session()
        progress = ProgressState(score_history=[0.33, 0.33, 0.33])
        result = checker.check_pre_routing("coba lagi", session, progress)
        assert result.should_escalate is True
        assert result.rule_name == "stagnation"

    def test_improving_scores_no_stagnation(self, checker):
        session = make_session()
        progress = ProgressState(score_history=[0.2, 0.33, 0.5])
        result = checker.check_pre_routing("coba lagi", session, progress)
        assert result.should_escalate is False


class TestIdleTurns:
    def test_idle_turns_triggers(self, checker):
        session = make_session(turn_count=8)
        progress = ProgressState(last_field_filled_turn=3)
        result = checker.check_pre_routing("hmm ok", session, progress)
        assert result.should_escalate is True
        assert result.rule_name == "idle_turns"

    def test_recent_field_no_idle(self, checker):
        session = make_session(turn_count=5)
        progress = ProgressState(last_field_filled_turn=3)
        result = checker.check_pre_routing("hmm ok", session, progress)
        assert result.should_escalate is False
```

### Step 2: Buat `tests/test_progress_tracker.py`

```python
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
```

### Step 3: Jalankan tests

```bash
.\venv\Scripts\pytest.exe tests/test_escalation_checker.py tests/test_progress_tracker.py -v
```

## 6. Output yang Diharapkan

```
tests/test_escalation_checker.py::TestAbsoluteMaxTurns::test_at_max_turns_triggers PASSED
tests/test_escalation_checker.py::TestLazyPattern::test_first_lazy_tolerated PASSED
...
tests/test_progress_tracker.py::TestProgressTracker::test_get_creates_new_state PASSED
...
====================== 18+ passed ======================
```

## 7. Dependencies

- **Task 02** — `EscalationConfig`
- **Task 03** — `EscalationChecker`
- **Task 04** — `ProgressTracker`
- **Task 01** — `ProgressState`, `EscalationDecision`

## 8. Acceptance Criteria

- [ ] `test_escalation_checker.py` → 12+ tests PASSED
- [ ] `test_progress_tracker.py` → 6+ tests PASSED
- [ ] Semua 5 escalation rules ter-cover
- [ ] Edge cases ter-cover: toleransi, streak reset, case insensitive
- [ ] Tidak butuh external services (pure unit tests)

## 9. Estimasi

**Medium** — ~1.5 jam
