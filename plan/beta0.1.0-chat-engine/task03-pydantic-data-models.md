# Task 03 — Pydantic Data Models

## 1. Judul Task

Buat semua Pydantic model untuk TOR data, session, chat messages, requests, dan responses.

## 2. Deskripsi

Mendefinisikan semua data structure (schema) yang dipakai di seluruh Chat Engine. Ini termasuk model untuk data TOR yang dikumpulkan, respons dari LLM, state session, pesan chat, serta request/response API.

## 3. Tujuan Teknis

- Semua Pydantic models terdefinisi dan bisa di-import
- Schema request/response API siap dipakai di endpoint
- Model `TORData` punya method `filled_fields()` dan `missing_fields()`
- Constants `REQUIRED_FIELDS` dan `OPTIONAL_FIELDS` terdefinisi

## 4. Scope

### Yang dikerjakan
- `app/models/tor.py` — TORData, LLMParsedResponse
- `app/models/session.py` — Session, ChatMessage
- `app/models/requests.py` — ChatRequest
- `app/models/responses.py` — ChatResponse, SessionState, SessionDetailResponse, ErrorResponse

### Yang tidak dikerjakan
- Database logic (hanya schema, bukan query)
- Endpoint logic

## 5. Langkah Implementasi

### Step 1: Buat `app/models/tor.py`

```python
from pydantic import BaseModel, Field
from typing import Literal

REQUIRED_FIELDS = ["judul", "latar_belakang", "tujuan", "ruang_lingkup", "output", "timeline"]
OPTIONAL_FIELDS = ["estimasi_biaya"]


class TORData(BaseModel):
    """Schema data TOR yang dikumpulkan selama chat."""
    judul: str | None = None
    latar_belakang: str | None = None
    tujuan: str | None = None
    ruang_lingkup: str | None = None
    output: str | None = None
    timeline: str | None = None
    estimasi_biaya: str | None = None

    def filled_fields(self) -> list[str]:
        """Return list field required yang sudah terisi."""
        return [f for f in REQUIRED_FIELDS if getattr(self, f) is not None]

    def missing_fields(self) -> list[str]:
        """Return list field required yang masih kosong."""
        return [f for f in REQUIRED_FIELDS if getattr(self, f) is None]


class LLMParsedResponse(BaseModel):
    """Schema respons JSON yang diharapkan dari local LLM."""
    status: Literal["NEED_MORE_INFO", "READY_TO_GENERATE", "ESCALATE_TO_GEMINI"]
    message: str
    data: TORData | None = None
    extracted_so_far: TORData | None = None
    partial_data: TORData | None = None
    missing_fields: list[str] | None = None
    reason: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
```

### Step 2: Buat `app/models/session.py`

```python
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
```

### Step 3: Buat `app/models/requests.py`

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=5000)
```

### Step 4: Buat `app/models/responses.py`

```python
from pydantic import BaseModel
from typing import Literal
from app.models.tor import TORData


class SessionState(BaseModel):
    status: str
    turn_count: int
    completeness_score: float
    filled_fields: list[str]
    missing_fields: list[str]


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
```

### Step 5: Buat `app/models/__init__.py` dengan re-exports

```python
from app.models.tor import TORData, LLMParsedResponse, REQUIRED_FIELDS, OPTIONAL_FIELDS
from app.models.session import Session, ChatMessage
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, SessionState, SessionDetailResponse, ErrorResponse
```

## 6. Output yang Diharapkan

```python
from app.models import TORData, REQUIRED_FIELDS

data = TORData(judul="Workshop AI", tujuan="Meningkatkan kompetensi")
print(data.filled_fields())   # ["judul", "tujuan"]
print(data.missing_fields())  # ["latar_belakang", "ruang_lingkup", "output", "timeline"]

from app.models import ChatRequest
req = ChatRequest(message="Halo")       # OK
req = ChatRequest(message="")           # ValidationError: min_length=1
```

## 7. Dependencies

- **Task 01** — Pydantic sudah terinstall

## 8. Acceptance Criteria

- [ ] `TORData()` bisa dibuat tanpa argumen (semua field None)
- [ ] `TORData.filled_fields()` return list field yang tidak None
- [ ] `TORData.missing_fields()` return list field yang masih None
- [ ] `REQUIRED_FIELDS` berisi 6 item: judul, latar_belakang, tujuan, ruang_lingkup, output, timeline
- [ ] `OPTIONAL_FIELDS` berisi 1 item: estimasi_biaya
- [ ] `LLMParsedResponse` memvalidasi bahwa `status` hanya boleh salah satu dari 3 nilai
- [ ] `LLMParsedResponse` memvalidasi bahwa `confidence` harus 0.0 - 1.0
- [ ] `ChatRequest(message="")` menghasilkan `ValidationError`
- [ ] `ChatRequest(message="a" * 5001)` menghasilkan `ValidationError`
- [ ] `ChatRequest(message="valid")` berhasil
- [ ] `Session` punya default `TORData()` untuk `extracted_data`
- [ ] `ChatResponse` punya default `type="chat"`
- [ ] Semua model bisa di-import dari `app.models`

## 9. Estimasi

**Low** — ~1 jam
