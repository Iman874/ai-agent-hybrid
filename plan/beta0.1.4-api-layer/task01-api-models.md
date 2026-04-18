# Task 01 — API Response Models: HybridAPIResponse, SessionState, HealthResponse

## 1. Judul Task

Buat Pydantic response models untuk unified API: `HybridRequest`, `HybridAPIResponse`, `SessionState`, `HealthResponse`, `ComponentHealth`, `ErrorResponse`.

## 2. Deskripsi

Definisikan semua Pydantic models yang dipakai oleh client-facing endpoints. Model ini menjadi contract API antara backend dan frontend (Streamlit/browser). `HybridAPIResponse` menyatukan semua response type (chat + generate) menjadi satu format.

## 3. Tujuan Teknis

- `HybridRequest` — body request untuk `/api/v1/hybrid`
- `SessionState` — state ringkas session (status, turn, completeness, fields)
- `HybridAPIResponse` — unified response (chat atau generate)
- `HealthResponse` + `ComponentHealth` — health check response
- `ErrorResponse` + `ErrorDetail` — error format standar

## 4. Scope

### Yang dikerjakan
- `app/models/api.py` — semua API-facing models

### Yang tidak dikerjakan
- Endpoint logic (itu task lain)
- Internal models (sudah ada dari beta sebelumnya)

## 5. Langkah Implementasi

### Step 1: Buat `app/models/api.py`

```python
from pydantic import BaseModel, Field
from typing import Literal
from app.models.routing import HybridOptions, EscalationInfo
from app.models.generate import TORDocument
from app.models.tor import TORData


class HybridRequest(BaseModel):
    """Request body untuk POST /api/v1/hybrid."""
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=5000)
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
```

### Step 2: Verifikasi

```python
from app.models.api import HybridRequest, HybridAPIResponse, SessionState, HealthResponse, ComponentHealth

req = HybridRequest(message="Buat TOR workshop AI")
assert req.session_id is None
assert req.message == "Buat TOR workshop AI"

state = SessionState(status="NEED_MORE_INFO", turn_count=2, completeness_score=0.33)
resp = HybridAPIResponse(
    session_id="test", type="chat", message="Apa tujuannya?", state=state
)
assert resp.type == "chat"

health = HealthResponse(
    status="healthy", version="0.1.0", uptime_seconds=42.0,
    components={"ollama": ComponentHealth(status="up", latency_ms=12.3)}
)
assert health.status == "healthy"

print("ALL API MODEL TESTS PASSED")
```

## 6. Output yang Diharapkan

Semua model bisa di-instantiate dan di-serialize ke JSON.

## 7. Dependencies

- **beta0.1.2 Task 01** — `TORDocument` model
- **beta0.1.3 Task 01** — `HybridOptions`, `EscalationInfo` models

## 8. Acceptance Criteria

- [ ] `HybridRequest` memiliki `session_id`, `message` (1-5000 chars), `options`
- [ ] `HybridAPIResponse` memiliki `session_id`, `type`, `message`, `state`, `tor_document`, `escalation_info`
- [ ] `SessionState` memiliki `status`, `turn_count`, `completeness_score`, `filled_fields`, `missing_fields`
- [ ] `HealthResponse` memiliki `status`, `version`, `uptime_seconds`, `components`
- [ ] Semua model bisa di-serialize ke JSON

## 9. Estimasi

**Low** — ~30 menit
