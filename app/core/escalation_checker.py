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
