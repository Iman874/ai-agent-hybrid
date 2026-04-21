from pydantic import BaseModel, Field
from typing import Literal
from app.models.routing import HybridOptions, EscalationInfo
from app.models.generate import TORDocument
from app.models.tor import TORData


class ModelCapabilitiesSchema(BaseModel):
    """Kemampuan model LLM — dikirim ke frontend via GET /models."""
    supports_text: bool = True
    supports_image_input: bool = False
    supports_streaming: bool = True


class HybridRequest(BaseModel):
    """Request body untuk POST /api/v1/hybrid."""
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=5000)
    images: list[str] | None = None  # base64-encoded image data
    options: HybridOptions | None = None


class SessionState(BaseModel):
    """State ringkas session untuk API response."""
    status: str
    turn_count: int = 0
    completeness_score: float = 0.0
    filled_fields: list[str] = []
    missing_fields: list[str] = []


class HybridAPIResponse(BaseModel):
    """Unified response untuk semua hybrid interactions."""
    session_id: str
    type: Literal["chat", "generate"]
    message: str
    state: SessionState
    extracted_data: TORData | None = None
    tor_document: TORDocument | None = None
    escalation_info: EscalationInfo | None = None
    cached: bool = False


class ComponentHealth(BaseModel):
    status: Literal["up", "down", "degraded"]
    details: dict | None = None
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    components: dict[str, ComponentHealth]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: str | None = None
    retry_after_seconds: int | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
