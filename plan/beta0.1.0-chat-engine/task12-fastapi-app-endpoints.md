# Task 12 — FastAPI Application & REST Endpoints

## 1. Judul Task

Setup FastAPI application, lifespan event, router, dan implementasi 3 endpoint: `/health`, `/chat`, `/session/{id}`.

## 2. Deskripsi

Membuat FastAPI app entry point yang menginisialisasi semua service saat startup, mendaftarkan routes, dan meng-expose 3 REST endpoint untuk Chat Engine module. Termasuk global error handler dan CORS middleware.

## 3. Tujuan Teknis

- `app/main.py` bisa dijalankan dengan `uvicorn app.main:app --reload`
- Database auto-init saat startup
- Semua service (ChatService, SessionManager, dll) di-wire di lifespan
- 3 endpoint berfungsi: health, chat, session
- Error handling: custom exceptions → JSON error response
- Swagger docs otomatis di `/docs`

## 4. Scope

### Yang dikerjakan
- `app/main.py` — FastAPI app + lifespan + CORS + error handlers
- `app/api/router.py` — central router
- `app/api/routes/health.py` — `GET /api/v1/health`
- `app/api/routes/chat.py` — `POST /api/v1/chat`
- `app/api/routes/session.py` — `GET /api/v1/session/{session_id}`

### Yang tidak dikerjakan
- Endpoint hybrid (itu beta0.1.4)
- Endpoint generate (itu beta0.1.2)
- Endpoint RAG ingest (itu beta0.1.1)

## 5. Langkah Implementasi

### Step 1: Buat `app/api/routes/health.py`

```python
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Basic health check."""
    return {
        "status": "healthy",
        "app_name": request.app.state.settings.app_name,
        "ollama_model": request.app.state.settings.ollama_chat_model,
    }
```

### Step 2: Buat `app/api/routes/chat.py`

```python
from fastapi import APIRouter, Request

from app.models.requests import ChatRequest
from app.models.responses import ChatResponse, SessionState

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest, request: Request):
    """
    Kirim pesan ke Chat Engine. Auto-create session baru jika session_id null.

    Body:
    - session_id (optional): UUID session yang sudah ada
    - message (required): Pesan user (1-5000 chars)
    """
    chat_service = request.app.state.chat_service

    result = await chat_service.process_message(
        session_id=body.session_id,
        message=body.message,
        rag_context=None,  # RAG belum ada di beta0.1.0
    )

    return ChatResponse(
        session_id=result.session_id,
        type="chat",
        message=result.message,
        state=SessionState(
            status=result.status,
            turn_count=result.completeness_score,  # TODO: fix di integration
            completeness_score=result.completeness_score,
            filled_fields=result.extracted_data.filled_fields(),
            missing_fields=result.missing_fields,
        ),
        extracted_data=result.extracted_data,
    )
```

### Step 3: Buat `app/api/routes/session.py`

```python
from fastapi import APIRouter, Request

from app.models.responses import SessionDetailResponse

router = APIRouter()


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, request: Request):
    """Get detail session beserta chat history."""
    chat_service = request.app.state.chat_service

    session = await chat_service.get_session(session_id)
    history = await chat_service.get_chat_history(session_id)

    return SessionDetailResponse(
        id=session.id,
        created_at=str(session.created_at),
        updated_at=str(session.updated_at),
        state=session.state,
        turn_count=session.turn_count,
        completeness_score=session.completeness_score,
        extracted_data=session.extracted_data,
        chat_history=[
            {
                "role": msg.role,
                "content": msg.content,
                "parsed_status": msg.parsed_status,
                "timestamp": str(msg.timestamp),
            }
            for msg in history
        ],
        generated_tor=session.generated_tor,
        metadata={
            "gemini_calls_count": session.gemini_calls_count,
            "total_tokens_local": session.total_tokens_local,
            "total_tokens_gemini": session.total_tokens_gemini,
        },
    )
```

### Step 4: Buat `app/api/router.py`

```python
from fastapi import APIRouter

from app.api.routes import health, chat, session

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(session.router, tags=["Session"])
```

### Step 5: Buat `app/main.py`

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings
from app.api.router import api_router
from app.db.database import init_db
from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.services.chat_service import ChatService
from app.utils.errors import (
    AppError,
    OllamaConnectionError,
    OllamaTimeoutError,
    SessionNotFoundError,
    LLMParseError,
)
from app.utils.logger import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown."""
    settings = Settings()
    app.state.settings = settings

    logger.info(f"Starting {settings.app_name}...")

    # Init database
    await init_db(settings.session_db_path)
    logger.info("Database initialized")

    # Init services
    ollama_provider = OllamaProvider(settings)
    session_mgr = SessionManager(settings.session_db_path)

    app.state.chat_service = ChatService(
        ollama=ollama_provider,
        session_mgr=session_mgr,
        prompt_builder=PromptBuilder(),
        parser=ResponseParser(),
    )

    logger.info(
        f"{settings.app_name} ready! "
        f"Model: {settings.ollama_chat_model}, "
        f"DB: {settings.session_db_path}"
    )

    yield  # App is running

    logger.info(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title="AI Agent Hybrid — Chat Engine",
    description="Local LLM interviewer for TOR data collection.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Global Error Handlers ===

@app.exception_handler(SessionNotFoundError)
async def handle_session_not_found(request: Request, exc: SessionNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": exc.code, "message": exc.message, "session_id": exc.session_id}},
    )

@app.exception_handler(OllamaConnectionError)
async def handle_ollama_connection(request: Request, exc: OllamaConnectionError):
    return JSONResponse(
        status_code=503,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )

@app.exception_handler(OllamaTimeoutError)
async def handle_ollama_timeout(request: Request, exc: OllamaTimeoutError):
    return JSONResponse(
        status_code=504,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )

@app.exception_handler(LLMParseError)
async def handle_llm_parse(request: Request, exc: LLMParseError):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )

@app.exception_handler(Exception)
async def handle_generic(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "E999", "message": "Internal server error."}},
    )

# === Routes ===
app.include_router(api_router, prefix="/api/v1")
```

### Step 6: Jalankan & test

```bash
# Start server
uvicorn app.main:app --reload --port 8000

# Test health
curl http://localhost:8000/api/v1/health

# Test chat (session baru)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Saya mau buat TOR untuk workshop AI"}'

# Test session detail (gunakan session_id dari response)
curl http://localhost:8000/api/v1/session/SESSION_ID

# Test error: session not found
curl http://localhost:8000/api/v1/session/non-existent

# Swagger docs
# Open browser: http://localhost:8000/docs
```

## 6. Output yang Diharapkan

### Health Check:
```json
{"status": "healthy", "app_name": "ai-agent-hybrid", "ollama_model": "qwen2.5:7b-instruct"}
```

### Chat (200 OK):
```json
{
    "session_id": "550e8400-...",
    "type": "chat",
    "message": "Baik, workshop AI terdengar menarik...",
    "state": {"status": "NEED_MORE_INFO", "completeness_score": 0.17, ...},
    "extracted_data": {"judul": "Workshop AI", ...}
}
```

### Session Not Found (404):
```json
{"error": {"code": "E006", "message": "Session tidak ditemukan.", "session_id": "non-existent"}}
```

## 7. Dependencies

- **Task 01** — config.py
- **Task 02** — errors.py, logger.py
- **Task 03** — semua Pydantic models
- **Task 04** — init_db()
- **Task 05** — SessionManager
- **Task 07** — OllamaProvider
- **Task 08** — PromptBuilder
- **Task 09** — ResponseParser
- **Task 10** — completeness calculator
- **Task 11** — ChatService

## 8. Acceptance Criteria

- [ ] `uvicorn app.main:app --reload` berhasil start tanpa error
- [ ] Server log: "ai-agent-hybrid ready!"
- [ ] Database auto-created di `data/sessions.db` saat startup
- [ ] `GET /api/v1/health` return 200 dengan status healthy
- [ ] `POST /api/v1/chat` dengan body `{"message": "..."}` return 200 dengan ChatResponse
- [ ] `POST /api/v1/chat` dengan body `{"message": ""}` return 422 validation error
- [ ] `POST /api/v1/chat` dengan session_id return 200 (lanjut session)
- [ ] `GET /api/v1/session/{valid_id}` return 200 dengan session detail + chat history
- [ ] `GET /api/v1/session/{invalid_id}` return 404 dengan error E006
- [ ] Jika Ollama tidak berjalan: POST /chat return 503 dengan error E001
- [ ] Swagger docs tersedia di `/docs`
- [ ] CORS headers tersedia di response

## 9. Estimasi

**High** — ~3 jam
