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
        progress = ProgressState(last_field_filled_turn=8)
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
