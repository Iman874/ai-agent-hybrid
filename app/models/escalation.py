from pydantic import BaseModel


class EscalationDecision(BaseModel):
    should_escalate: bool
    rule_name: str | None = None
    reason: str | None = None
    confidence: float = 0.0


class ProgressState(BaseModel):
    """Tracking progress per session untuk stagnation detection."""
    score_history: list[float] = []
    last_field_filled_turn: int = 0
    lazy_strike_count: int = 0
    short_input_streak: int = 0
    previous_filled_count: int = 0
