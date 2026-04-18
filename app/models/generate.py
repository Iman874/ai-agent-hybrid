from pydantic import BaseModel
from typing import Literal


class TORMetadata(BaseModel):
    generated_by: str                    # "gemini-2.0-flash"
    mode: str                            # "standard" | "escalation"
    word_count: int
    generation_time_ms: int
    has_assumptions: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0


class TORDocument(BaseModel):
    format: str = "markdown"
    content: str
    metadata: TORMetadata


class GenerateRequest(BaseModel):
    session_id: str
    mode: Literal["standard", "escalation"] = "standard"
    force_regenerate: bool = False


class GenerateResponse(BaseModel):
    session_id: str
    type: Literal["generate"] = "generate"
    message: str
    tor_document: TORDocument
    cached: bool = False


class GeminiResponse(BaseModel):
    """Internal response dari GeminiProvider."""
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: int = 0


class ProcessedTOR(BaseModel):
    """Output dari PostProcessor."""
    content: str
    word_count: int
    has_assumptions: bool = False
    missing_sections: list[str] = []


class GenerateResult(BaseModel):
    """Internal result dari GenerateService."""
    session_id: str
    tor_document: TORDocument
    cached: bool = False
