from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from app.models.tor import TORData


class Session(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    state: Literal["NEW", "CHATTING", "READY", "ESCALATED", "GENERATING", "COMPLETED"]
    turn_count: int = 0
    completeness_score: float = 0.0
    extracted_data: TORData = TORData()
    generated_tor: str | None = None
    escalation_reason: str | None = None
    gemini_calls_count: int = 0
    total_tokens_local: int = 0
    total_tokens_gemini: int = 0


class ChatMessage(BaseModel):
    id: int | None = None
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    parsed_status: str | None = None
    timestamp: datetime | None = None
