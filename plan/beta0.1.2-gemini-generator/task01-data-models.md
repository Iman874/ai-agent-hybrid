# Task 01 — Pydantic Data Models untuk Gemini Generator

## 1. Judul Task

Buat data models Pydantic untuk modul Generate: `GenerateRequest`, `TORDocument`, `TORMetadata`, `GenerateResponse`, `GeminiResponse`, `ProcessedTOR`.

## 2. Deskripsi

Membuat semua model Pydantic yang akan dipakai di seluruh pipeline Gemini Generator. Model ini menjadi contract antara komponen: API endpoint ↔ GenerateService ↔ GeminiProvider ↔ PostProcessor ↔ Cache.

## 3. Tujuan Teknis

- `GenerateRequest` — input dari API endpoint
- `TORDocument` + `TORMetadata` — representasi dokumen TOR yang di-generate
- `GenerateResponse` — output ke client
- `GeminiResponse` — internal response dari GeminiProvider
- `ProcessedTOR` — output internal dari PostProcessor

## 4. Scope

### Yang dikerjakan
- `app/models/generate.py` — semua data models

### Yang tidak dikerjakan
- Logic/service apapun
- API endpoint

## 5. Langkah Implementasi

### Step 1: Buat `app/models/generate.py`

```python
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
```

### Step 2: Verifikasi

```python
from app.models.generate import GenerateRequest, TORDocument, TORMetadata, GenerateResponse

# Test instantiation
req = GenerateRequest(session_id="test-123")
assert req.mode == "standard"
assert req.force_regenerate is False

meta = TORMetadata(
    generated_by="gemini-2.0-flash", mode="standard",
    word_count=500, generation_time_ms=3000
)
doc = TORDocument(content="# TOR\n\nTest content", metadata=meta)
assert doc.format == "markdown"

resp = GenerateResponse(
    session_id="test-123", message="TOR berhasil dibuat.",
    tor_document=doc
)
assert resp.type == "generate"

print("ALL MODEL TESTS PASSED")
```

## 6. Output yang Diharapkan

Semua model bisa di-instantiate tanpa error dan sesuai dengan type hints.

## 7. Dependencies

- Tidak ada (model murni, standalone)

## 8. Acceptance Criteria

- [ ] `GenerateRequest` memiliki `session_id`, `mode`, `force_regenerate`
- [ ] `TORDocument` memiliki `format`, `content`, `metadata`
- [ ] `TORMetadata` memiliki semua field: `generated_by`, `mode`, `word_count`, `generation_time_ms`, `has_assumptions`, `prompt_tokens`, `completion_tokens`
- [ ] `GenerateResponse` memiliki `session_id`, `type`, `message`, `tor_document`, `cached`
- [ ] `GeminiResponse` memiliki `text`, `prompt_tokens`, `completion_tokens`, `duration_ms`
- [ ] `ProcessedTOR` memiliki `content`, `word_count`, `has_assumptions`, `missing_sections`
- [ ] Semua model bisa di-serialize ke JSON

## 9. Estimasi

**Low** — ~30 menit
