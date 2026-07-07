from enum import Enum
from pydantic import BaseModel, Field

from app.models.tor import TORData


class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    INTERVIEWER = "interviewer"
    WRITER = "writer"


class AgentContext(BaseModel):
    agent_type: AgentType
    user_message: str | None = None
    session_id: str = ""
    extracted_data: TORData = Field(default_factory=TORData)
    missing_fields: list[str] = Field(default_factory=list)
    completeness: float = 0.0
    turn_count: int = 0
    conversation_history: list[dict] = Field(default_factory=list)
    conversation_summary: str | None = None
    generated_tor: str | None = None
    rag_context: str | None = None
    chat_mode: str = "zen"


class AgentResult(BaseModel):
    agent: AgentType
    decision: str | None = None
    message: str | None = None
    data: TORData | None = None
    tor_content: str | None = None
    confidence: float = 0.0
    error: str | None = None
