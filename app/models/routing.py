from pydantic import BaseModel
from typing import Literal
from app.models.generate import GenerateResult


class HybridOptions(BaseModel):
    force_generate: bool = False
    language: str = "id"
    chat_mode: str = "local"  # "local" | "gemini"


class EscalationInfo(BaseModel):
    triggered_by: str                    # nama rule yang trigger
    reason: str                          # penjelasan human-readable
    turn_count: int                      # turn saat eskalasi terjadi
    completeness_at_escalation: float    # score saat eskalasi


class RoutingResult(BaseModel):
    session_id: str
    action_taken: Literal[
        "CHAT",
        "GENERATE_STANDARD",
        "GENERATE_ESCALATION",
        "FORCE_GENERATE",
    ]
    chat_response: object | None = None       # ChatResult (import circular prevention)
    generate_response: GenerateResult | None = None
    escalation_info: EscalationInfo | None = None
