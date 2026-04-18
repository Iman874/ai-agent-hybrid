# Task 11 — API Endpoint: POST /api/v1/generate & App Wiring

## 1. Judul Task

Buat endpoint `POST /api/v1/generate`, register ke router, dan init semua komponen Gemini Generator di `app/main.py` lifespan.

## 2. Deskripsi

Endpoint final yang menerima `GenerateRequest`, memanggil `GenerateService.generate_tor()`, dan return `GenerateResponse`. Juga melakukan wiring semua komponen baru di lifespan FastAPI.

## 3. Tujuan Teknis

- `POST /api/v1/generate` — accept `GenerateRequest`, return `GenerateResponse`
- Error handling: 400 (insufficient data), 429 (rate limit), 502 (Gemini error), 504 (timeout)
- Register ke `app/api/router.py` under tag "Generate"
- Init di `app/main.py` lifespan: `GeminiProvider`, `TORCache`, `CostController`, `GenerateService`
- Semua component ter-attach ke `app.state`

## 4. Scope

### Yang dikerjakan
- `app/api/routes/generate.py` — endpoint
- Update `app/api/router.py` — register generate router
- Update `app/main.py` — init dan wiring GenerateService di lifespan

### Yang tidak dikerjakan
- Business logic (sudah di GenerateService)

## 5. Langkah Implementasi

### Step 1: Buat `app/api/routes/generate.py`

```python
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.generate import GenerateRequest, GenerateResponse
from app.utils.errors import (
    RateLimitError, GeminiAPIError, GeminiTimeoutError, InsufficientDataError
)

logger = logging.getLogger("ai-agent-hybrid.api.generate")

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
async def generate_tor(request: Request, body: GenerateRequest):
    """
    Generate dokumen TOR via Gemini API.

    - **session_id**: ID session dari chat engine
    - **mode**: `standard` (data lengkap) atau `escalation` (data parsial)
    - **force_regenerate**: `true` untuk bypass cache
    """
    generate_service = request.app.state.generate_service

    try:
        result = await generate_service.generate_tor(
            session_id=body.session_id,
            mode=body.mode,
            force_regenerate=body.force_regenerate,
        )
    except InsufficientDataError as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )
    except RateLimitError as e:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": e.code, "message": e.message, "retry_after_seconds": 120}}
        )
    except GeminiTimeoutError as e:
        return JSONResponse(
            status_code=504,
            content={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )
    except GeminiAPIError as e:
        return JSONResponse(
            status_code=502,
            content={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )

    # Build response message
    if result.cached:
        message = "TOR disajikan dari cache."
    elif result.tor_document.metadata.mode == "escalation":
        message = "TOR telah dibuat berdasarkan informasi yang tersedia. Bagian yang ditandai [ASUMSI] dapat disesuaikan."
    else:
        message = "TOR berhasil dibuat berdasarkan informasi yang Anda berikan."

    return GenerateResponse(
        session_id=result.session_id,
        message=message,
        tor_document=result.tor_document,
        cached=result.cached,
    )
```

### Step 2: Update `app/api/router.py`

```python
from app.api.routes import health, chat, session, rag, generate  # tambah generate

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(session.router, tags=["Session"])
api_router.include_router(rag.router, tags=["RAG"])
api_router.include_router(generate.router, tags=["Generate"])  # tambah ini
```

### Step 3: Update `app/main.py` lifespan

Setelah inisialisasi RAGPipeline dan sebelum ChatService, tambahkan:

```python
from app.ai.gemini_provider import GeminiProvider
from app.core.gemini_prompt_builder import GeminiPromptBuilder
from app.core.post_processor import PostProcessor
from app.core.cost_controller import CostController
from app.db.repositories.cache_repo import TORCache
from app.services.generate_service import GenerateService

# Init Gemini Generator components
gemini_provider = GeminiProvider(settings)
tor_cache = TORCache(settings.session_db_path)
cost_controller = CostController(session_mgr, settings)

app.state.generate_service = GenerateService(
    gemini=gemini_provider,
    session_mgr=session_mgr,
    rag_pipeline=rag_pipeline,
    prompt_builder=GeminiPromptBuilder(),
    post_processor=PostProcessor(),
    cache=tor_cache,
    cost_ctrl=cost_controller,
)
logger.info("Generate Service initialized")
```

### Step 4: Verifikasi

```python
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    # Test 1: Health check still works
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    print("Test 1: health OK")

    # Test 2: Generate without valid session → 404/500
    resp2 = client.post("/api/v1/generate", json={
        "session_id": "nonexistent-session",
        "mode": "standard"
    })
    # Should get error since session doesn't exist
    assert resp2.status_code in (404, 500)
    print(f"Test 2: invalid session → {resp2.status_code}")

    print("ENDPOINT WIRING TESTS PASSED")
```

## 6. Output yang Diharapkan

Endpoint accessible di Swagger `/docs` under tag "Generate". Server start tanpa error.

## 7. Dependencies

- **Task 10** — `GenerateService`
- **Task 04** — `GeminiProvider`
- **Task 08** — `TORCache`
- **Task 09** — `CostController`

## 8. Acceptance Criteria

- [ ] `POST /api/v1/generate` muncul di Swagger `/docs`
- [ ] Invalid session → error response (404 atau 500)
- [ ] Rate limit hit → 429 response
- [ ] Insufficient data → 400 response
- [ ] Gemini timeout → 504 response
- [ ] Gemini API error → 502 response
- [ ] Server startup tidak error setelah wiring
- [ ] Response message disesuaikan berdasarkan cached/escalation/standard

## 9. Estimasi

**Medium** — ~2 jam
