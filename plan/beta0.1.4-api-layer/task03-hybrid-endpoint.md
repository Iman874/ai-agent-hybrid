# Task 03 — Hybrid Endpoint: POST /api/v1/hybrid

## 1. Judul Task

Buat endpoint `POST /api/v1/hybrid` — entry point utama yang menerima pesan user dan memanggil `DecisionEngine.route()` untuk auto-routing.

## 2. Deskripsi

Endpoint utama seluruh sistem. Menerima `HybridRequest`, memanggil `DecisionEngine.route()`, lalu convert `RoutingResult` ke `HybridAPIResponse`. Ini adalah satu-satunya endpoint yang perlu dipanggil oleh frontend.

## 3. Tujuan Teknis

- `POST /api/v1/hybrid` — accept `HybridRequest`, return `HybridAPIResponse`
- `_convert_to_api_response(result) → HybridAPIResponse` — konversi internal model ke API model
- Error handling: delegate ke global error handlers
- Register ke `app/api/router.py` under tag "Hybrid"

## 4. Scope

### Yang dikerjakan
- `app/api/routes/hybrid.py` — endpoint + converter
- Update `app/api/router.py` — register hybrid router

### Yang tidak dikerjakan
- DecisionEngine logic (sudah ada)
- Error handler (sudah ada / task terpisah)

## 5. Langkah Implementasi

### Step 1: Buat `app/api/routes/hybrid.py`

```python
import logging
from fastapi import APIRouter, Request
from app.models.api import HybridRequest, HybridAPIResponse, SessionState
from app.models.routing import RoutingResult

logger = logging.getLogger("ai-agent-hybrid.api.hybrid")

router = APIRouter()


@router.post("/hybrid", response_model=HybridAPIResponse)
async def hybrid_endpoint(request: Request, body: HybridRequest):
    """
    Main endpoint. Kirim pesan, sistem otomatis routing antara
    chat (local LLM) dan generate (Gemini).
    """
    decision_engine = request.app.state.decision_engine

    result = await decision_engine.route(
        session_id=body.session_id,
        message=body.message,
        options=body.options,
    )

    return _convert_to_api_response(result)


def _convert_to_api_response(result: RoutingResult) -> HybridAPIResponse:
    """Convert internal RoutingResult ke API response."""
    if result.generate_response:
        # Generate response (standard atau escalation)
        chat = result.chat_response
        return HybridAPIResponse(
            session_id=result.session_id,
            type="generate",
            message=chat.message if chat else "TOR berhasil dibuat.",
            state=SessionState(
                status="COMPLETED",
                turn_count=chat.completeness_score if chat else 0,
                completeness_score=chat.completeness_score if chat else 1.0,
                filled_fields=chat.extracted_data.filled_fields() if chat else [],
                missing_fields=chat.missing_fields if chat else [],
            ),
            extracted_data=chat.extracted_data if chat else None,
            tor_document=result.generate_response.tor_document,
            escalation_info=result.escalation_info,
            cached=result.generate_response.cached,
        )
    else:
        # Chat response
        chat = result.chat_response
        return HybridAPIResponse(
            session_id=result.session_id,
            type="chat",
            message=chat.message,
            state=SessionState(
                status=chat.status,
                turn_count=0,
                completeness_score=chat.completeness_score,
                filled_fields=chat.extracted_data.filled_fields(),
                missing_fields=chat.missing_fields,
            ),
            extracted_data=chat.extracted_data,
        )
```

### Step 2: Update `app/api/router.py`

```python
from app.api.routes import health, chat, session, rag, generate, hybrid

api_router = APIRouter()
api_router.include_router(hybrid.router, tags=["Hybrid"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(generate.router, tags=["Generate"])
api_router.include_router(session.router, tags=["Session"])
api_router.include_router(rag.router, tags=["RAG"])
api_router.include_router(health.router, tags=["Health"])
```

### Step 3: Verifikasi

Server start tanpa error, endpoint muncul di Swagger `/docs`.

## 6. Output yang Diharapkan

`POST /api/v1/hybrid` accessible di Swagger, menerima JSON body dan return `HybridAPIResponse`.

## 7. Dependencies

- **Task 01** — `HybridRequest`, `HybridAPIResponse`, `SessionState`
- **beta0.1.3** — `DecisionEngine` (already wired di `app.state`)

## 8. Acceptance Criteria

- [ ] `POST /api/v1/hybrid` muncul di Swagger `/docs`
- [ ] Session baru dibuat jika `session_id` null
- [ ] Chat response → type="chat"
- [ ] Generate response → type="generate" dengan `tor_document`
- [ ] Escalation info ter-attach jika eskalasi terjadi

## 9. Estimasi

**Medium** — ~1.5 jam
