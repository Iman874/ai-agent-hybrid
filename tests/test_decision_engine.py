"""
Integration tests DecisionEngine.
Tests routing logic with real SQLite DB.
"""
import pytest
import pytest_asyncio
from datetime import datetime

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def decision_setup(tmp_path):
    """Setup DecisionEngine with test DB."""
    test_db = str(tmp_path / "test_decision.db")
    from app.db.database import init_db
    await init_db(test_db)

    from app.config import Settings
    from app.core.session_manager import SessionManager
    from app.core.escalation_config import EscalationConfig
    from app.core.escalation_checker import EscalationChecker
    from app.core.progress_tracker import ProgressTracker
    from app.db.repositories.escalation_repo import EscalationLogger

    settings = Settings()
    session_mgr = SessionManager(test_db)
    escalation_checker = EscalationChecker(EscalationConfig())
    progress_tracker = ProgressTracker()
    escalation_logger = EscalationLogger(test_db)

    return {
        "session_mgr": session_mgr,
        "checker": escalation_checker,
        "tracker": progress_tracker,
        "esc_logger": escalation_logger,
    }


async def test_escalation_checker_with_real_session(decision_setup):
    """Test EscalationChecker with session from real DB."""
    session_mgr = decision_setup["session_mgr"]
    checker = decision_setup["checker"]
    from app.models.escalation import ProgressState

    # Create session
    session = await session_mgr.create()
    await session_mgr.update(session.id, state="CHATTING", turn_count=3)
    session = await session_mgr.get(session.id)

    # Normal message — no escalation
    progress = ProgressState()
    result = checker.check_pre_routing("Peserta 30 orang ASN", session, progress)
    assert result.should_escalate is False

    # Lazy first → tolerated
    result2 = checker.check_pre_routing("terserah", session, progress)
    assert result2.should_escalate is False
    assert progress.lazy_strike_count == 1

    # Lazy second → escalate
    result3 = checker.check_pre_routing("gak tau", session, progress)
    assert result3.should_escalate is True
    assert result3.rule_name == "lazy_pattern"


async def test_escalation_logger_persists(decision_setup):
    """Test EscalationLogger writes to SQLite."""
    session_mgr = decision_setup["session_mgr"]
    esc_logger = decision_setup["esc_logger"]
    from app.models.escalation import EscalationDecision

    session = await session_mgr.create()
    decision = EscalationDecision(
        should_escalate=True,
        rule_name="lazy_pattern",
        reason="User menunjukkan pola tidak kooperatif (2x lazy response)",
        confidence=0.9,
    )

    await esc_logger.log(session.id, decision, 5, 0.33, "gak tau")

    history = await esc_logger.get_history(session.id)
    assert len(history) == 1
    assert history[0]["rule_name"] == "lazy_pattern"
    assert history[0]["turn_count"] == 5


async def test_progress_tracker_stagnation_scenario(decision_setup):
    """Test full stagnation scenario: 3 turns without progress."""
    checker = decision_setup["checker"]
    tracker = decision_setup["tracker"]
    session_mgr = decision_setup["session_mgr"]

    session = await session_mgr.create()
    await session_mgr.update(session.id, state="CHATTING", turn_count=5)
    session = await session_mgr.get(session.id)

    # Simulate 3 turns with same score
    tracker.update_after_chat(session.id, 0.33, 2)
    tracker.update_after_chat(session.id, 0.33, 2)
    tracker.update_after_chat(session.id, 0.33, 2)

    progress = tracker.get(session.id)
    result = checker.check_pre_routing("apa lagi ya", session, progress)
    assert result.should_escalate is True
    assert result.rule_name == "stagnation"


async def test_completed_session_returns_info(decision_setup):
    """Test that completed session is handled gracefully."""
    session_mgr = decision_setup["session_mgr"]

    session = await session_mgr.create()
    await session_mgr.update(
        session.id, state="COMPLETED",
        generated_tor="# TOR\nIsi TOR yang sudah jadi."
    )
    session = await session_mgr.get(session.id)

    assert session.state == "COMPLETED"
    assert session.generated_tor is not None
