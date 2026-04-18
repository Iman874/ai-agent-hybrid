# Task 03 — EscalationChecker: Deteksi Kapan Harus Eskalasi

## 1. Judul Task

Implementasikan `EscalationChecker` — class yang menjalankan 5 escalation rules dan mengembalikan `EscalationDecision`.

## 2. Deskripsi

EscalationChecker menganalisis pesan user SEBELUM dikirim ke LLM. Ia menjalankan 5 rules berurutan (priority order): absolute max turns → lazy pattern → short input → stagnation → idle turns. Jika salah satu match, return `should_escalate=True`.

## 3. Tujuan Teknis

- `check_pre_routing(message, session, progress) → EscalationDecision`
- `_match_lazy_pattern(message) → bool` — regex matching
- 5 rules berurutan sesuai prioritas
- Side effect: update `progress.lazy_strike_count` dan `progress.short_input_streak`

## 4. Scope

### Yang dikerjakan
- `app/core/escalation_checker.py` — class `EscalationChecker`

### Yang tidak dikerjakan
- Handle escalation (itu di DecisionEngine)
- Logging ke database

## 5. Langkah Implementasi

### Step 1: Buat `app/core/escalation_checker.py`

```python
import re
import logging
from app.core.escalation_config import EscalationConfig
from app.models.escalation import EscalationDecision, ProgressState
from app.models.session import Session

logger = logging.getLogger("ai-agent-hybrid.escalation")


class EscalationChecker:
    def __init__(self, config: EscalationConfig | None = None):
        self.config = config or EscalationConfig()
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.config.lazy_patterns
        ]

    def check_pre_routing(
        self,
        message: str,
        session: Session,
        progress: ProgressState,
    ) -> EscalationDecision:
        """
        Check SEBELUM kirim ke LLM.
        Returns EscalationDecision.
        """
        # Rule 1: Absolute max turns
        if session.turn_count >= self.config.absolute_max_turns:
            return EscalationDecision(
                should_escalate=True,
                rule_name="absolute_max_turns",
                reason=f"Batas maksimum turn ({self.config.absolute_max_turns}) tercapai",
                confidence=1.0,
            )

        # Rule 2: Lazy pattern detection
        is_lazy = self._match_lazy_pattern(message)
        if is_lazy:
            new_strike = progress.lazy_strike_count + 1
            if new_strike > self.config.lazy_tolerance:
                return EscalationDecision(
                    should_escalate=True,
                    rule_name="lazy_pattern",
                    reason=f"User menunjukkan pola tidak kooperatif "
                           f"({new_strike}x lazy response, toleransi: {self.config.lazy_tolerance})",
                    confidence=0.9,
                )
            # Belum melewati toleransi — update strike, lanjut ke LLM
            progress.lazy_strike_count = new_strike

        # Rule 3: Short input consecutive
        is_short = len(message.strip()) <= self.config.short_input_max_chars
        if is_short and session.turn_count >= 2:
            new_streak = progress.short_input_streak + 1
            if new_streak >= self.config.short_input_consecutive:
                return EscalationDecision(
                    should_escalate=True,
                    rule_name="short_input_consecutive",
                    reason=f"{new_streak}x berturut-turut jawaban sangat pendek "
                           f"(≤{self.config.short_input_max_chars} karakter)",
                    confidence=0.8,
                )
            progress.short_input_streak = new_streak
        else:
            progress.short_input_streak = 0  # reset streak

        # Rule 4: Stagnation (score tidak naik selama N turn)
        if len(progress.score_history) >= self.config.stagnation_turns:
            recent_scores = progress.score_history[-self.config.stagnation_turns:]
            if all(s == recent_scores[0] for s in recent_scores) and recent_scores[0] < 1.0:
                return EscalationDecision(
                    should_escalate=True,
                    rule_name="stagnation",
                    reason=f"Tidak ada progress data baru selama "
                           f"{self.config.stagnation_turns} turn "
                           f"(score tetap {recent_scores[0]:.2f})",
                    confidence=0.85,
                )

        # Rule 5: Idle turns (lama sejak field terakhir terisi)
        idle_turns = session.turn_count - progress.last_field_filled_turn
        if idle_turns >= self.config.max_idle_turns:
            return EscalationDecision(
                should_escalate=True,
                rule_name="idle_turns",
                reason=f"{idle_turns} turn tanpa field baru terisi "
                       f"(max idle: {self.config.max_idle_turns})",
                confidence=0.7,
            )

        # No escalation needed
        return EscalationDecision(should_escalate=False)

    def _match_lazy_pattern(self, message: str) -> bool:
        """Check if message matches any lazy pattern."""
        text = message.strip().lower()
        return any(pattern.search(text) for pattern in self.compiled_patterns)
```

### Step 2: Verifikasi

```python
from datetime import datetime
from app.core.escalation_checker import EscalationChecker
from app.core.escalation_config import EscalationConfig
from app.models.escalation import ProgressState
from app.models.session import Session

config = EscalationConfig()
checker = EscalationChecker(config)
now = datetime.utcnow()

def make_session(**kwargs):
    defaults = dict(id="test", created_at=now, updated_at=now, state="CHATTING", turn_count=3)
    defaults.update(kwargs)
    return Session(**defaults)

# Test 1: Normal message → no escalation
progress = ProgressState()
session = make_session()
result = checker.check_pre_routing("Timeline nya 3 hari di bulan Juli", session, progress)
assert result.should_escalate is False
print("Test 1: normal message OK")

# Test 2: Lazy first time → tolerated
progress2 = ProgressState()
result2 = checker.check_pre_routing("terserah aja", session, progress2)
assert result2.should_escalate is False
assert progress2.lazy_strike_count == 1
print("Test 2: lazy first time tolerated OK")

# Test 3: Lazy second time → escalate
progress3 = ProgressState(lazy_strike_count=1)
result3 = checker.check_pre_routing("gak tau", session, progress3)
assert result3.should_escalate is True
assert result3.rule_name == "lazy_pattern"
print("Test 3: lazy second time triggers OK")

# Test 4: Max turns → escalate
session4 = make_session(turn_count=10)
progress4 = ProgressState()
result4 = checker.check_pre_routing("halo", session4, progress4)
assert result4.should_escalate is True
assert result4.rule_name == "absolute_max_turns"
print("Test 4: max turns OK")

# Test 5: Short input consecutive
progress5 = ProgressState(short_input_streak=1)
result5 = checker.check_pre_routing("ok", session, progress5)
assert result5.should_escalate is True
assert result5.rule_name == "short_input_consecutive"
print("Test 5: short input OK")

# Test 6: Stagnation
progress6 = ProgressState(score_history=[0.33, 0.33, 0.33])
result6 = checker.check_pre_routing("coba lagi", session, progress6)
assert result6.should_escalate is True
assert result6.rule_name == "stagnation"
print("Test 6: stagnation OK")

print("ALL ESCALATION CHECKER TESTS PASSED")
```

## 6. Output yang Diharapkan

`EscalationDecision` yang menunjukkan apakah harus eskalasi, beserta rule_name dan reason.

## 7. Dependencies

- **Task 01** — `EscalationDecision`, `ProgressState` models
- **Task 02** — `EscalationConfig`
- **beta0.1.0** — `Session` model

## 8. Acceptance Criteria

- [ ] Rule absolute_max_turns: turn ≥ 10 → escalate
- [ ] Rule lazy_pattern: lazy pertama ditoleransi, lazy kedua escalate
- [ ] Rule short_input: 2x berturut ≤ 15 chars saat turn ≥ 2 → escalate
- [ ] Rule stagnation: score sama 3 turn berturut → escalate
- [ ] Rule idle_turns: 5+ turn tanpa field baru → escalate
- [ ] Normal message → tidak escalate
- [ ] Side effects: progress.lazy_strike_count dan short_input_streak ter-update

## 9. Estimasi

**Medium** — ~1.5 jam
