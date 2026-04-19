from pydantic import BaseModel
from typing import Literal
from app.models.tor import TORData


class SessionState(BaseModel):
    status: str
    turn_count: int
    completeness_score: float
    filled_fields: list[str]
    missing_fields: list[str]


class SessionListItem(BaseModel):
    id: str
    title: str | None = None
    state: str
    turn_count: int
    created_at: str
    updated_at: str
    has_tor: bool


class ChatResponse(BaseModel):
    session_id: str
    type: Literal["chat"] = "chat"
    message: str
    state: SessionState
    extracted_data: TORData


class SessionDetailResponse(BaseModel):
    id: str
    created_at: str
    updated_at: str
    state: str
    turn_count: int
    completeness_score: float
    extracted_data: TORData
    chat_history: list[dict]
    generated_tor: str | None = None
    metadata: dict


class ErrorResponse(BaseModel):
    error: dict
