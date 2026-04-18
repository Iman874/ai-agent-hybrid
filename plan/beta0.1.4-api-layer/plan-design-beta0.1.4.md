# Beta 0.1.4 — API & Integration Layer

> **Modul**: API Layer + Full System Integration
> **Versi**: beta0.1.4
> **Status**: Ready to Implement
> **Estimasi**: 2 hari kerja
> **Prasyarat**: beta0.1.0 s/d beta0.1.3 SEMUA sudah selesai

---

## 1. Overview

API Layer adalah **lem pengikat** seluruh sistem — ia menyatukan semua modul (Chat Engine, RAG, Gemini Generator, Decision Engine) menjadi satu aplikasi FastAPI yang siap dijalankan. Modul ini:

1. **Menginisialisasi** FastAPI application, middleware, CORS, dan lifespan events
2. **Mendaftarkan** semua route endpoints ke central router
3. **Menghubungkan** dependency injection: semua service, provider, dan repository di-wire menjadi satu
4. **Menyediakan** endpoint hybrid `/api/v1/hybrid` sebagai entry point utama
5. **Mengatur** error handling global, logging, dan health check
6. **Menjalankan** database migration saat startup

Ini adalah modul **terakhir** yang diimplementasi karena ia bergantung pada semua modul sebelumnya.

---

## 2. Scope

### ✅ Yang dikerjakan di modul ini

| Item | Detail |
|---|---|
| FastAPI App Setup | `app/main.py` — lifespan, middleware, CORS |
| Central Router | `app/api/router.py` — registrasi semua route modules |
| Hybrid Endpoint | `POST /api/v1/hybrid` — endpoint utama auto-routing |
| Health Endpoint | `GET /api/v1/health` — cek status semua dependencies |
| Dependency Injection | Wire semua services (ChatService, GenerateService, RAGPipeline, DecisionEngine) |
| Global Error Handler | Catch & format semua custom exceptions |
| Database Init | Auto-create tables saat startup |
| Logging Setup | Structured logging dengan request ID |
| CORS Configuration | Allow origins untuk frontend (Streamlit, browser) |
| `.env.example` | Template environment variables |
| `requirements.txt` | Complete dependency list |
| `Makefile` | Dev shortcuts (`make run`, `make test`, `make ingest`) |

### ❌ Yang TIDAK dikerjakan di modul ini

| Item | Alasan |
|---|---|
| Streamlit UI | Ditunda ke phase 6 (roadmap). API-only dulu. |
| Docker | Ditunda ke roadmap v1.0 |
| Authentication | Ditunda ke roadmap v0.4 |
| PDF export | Ditunda ke roadmap v1.0 |

---

## 3. Input / Output

### Input: Hybrid Endpoint (Entry Point Utama)

```json
POST /api/v1/hybrid
Content-Type: application/json

{
    "session_id": "string | null",
    "message": "string (1-5000 chars)",
    "options": {
        "force_generate": false,
        "language": "id"
    }
}
```

### Output: Unified Response

Tergantung routing result dari Decision Engine:

**Chat Response** (masih ngobrol):
```json
{
    "session_id": "550e8400-...",
    "type": "chat",
    "message": "Baik, workshop AI-nya berapa hari?",
    "state": {
        "status": "NEED_MORE_INFO",
        "turn_count": 2,
        "completeness_score": 0.33,
        "filled_fields": ["judul", "latar_belakang"],
        "missing_fields": ["tujuan", "ruang_lingkup", "output", "timeline"]
    },
    "extracted_data": { ... },
    "tor_document": null,
    "escalation_info": null
}
```

**Generate Response** (TOR jadi):
```json
{
    "session_id": "550e8400-...",
    "type": "generate",
    "message": "TOR berhasil dibuat!",
    "state": {
        "status": "COMPLETED",
        "turn_count": 4,
        "completeness_score": 1.0,
        "filled_fields": [...],
        "missing_fields": []
    },
    "extracted_data": { ... },
    "tor_document": {
        "format": "markdown",
        "content": "# TERM OF REFERENCE...",
        "metadata": {
            "generated_by": "gemini-2.0-flash",
            "mode": "standard",
            "word_count": 876,
            "generation_time_ms": 3200,
            "has_assumptions": false
        }
    },
    "escalation_info": null
}
```

---

## 4. Flow Logic

### Application Startup (Lifespan)

```
APPLICATION START
────────────────────

STEP 1: Load Configuration
    → Settings dari .env via Pydantic Settings
    → Validasi: GEMINI_API_KEY harus ada
    → Validasi: OLLAMA_BASE_URL accessible

STEP 2: Initialize Database
    → Connect ke SQLite (SESSION_DB_PATH)
    → Run migrations: 001_initial.sql, 002_gemini_tables.sql, 003_escalation_log.sql
    → WAL mode untuk concurrent access

STEP 3: Initialize AI Providers
    → OllamaProvider(settings) — test koneksi ke localhost:11434
    → GeminiProvider(settings) — test API key validity

STEP 4: Initialize RAG Pipeline
    → OllamaEmbedder(model=bge-m3)
    → ChromaVectorStore(path=./data/chroma_db)
    → Retriever + ContextFormatter
    → RAGPipeline(all_components)
    → IF ChromaDB init gagal: log warning, set rag_pipeline = None

STEP 5: Initialize Services
    → SessionManager(db_path)
    → ChatService(ollama, session_mgr, prompt_builder, parser)
    → GenerateService(gemini, session_mgr, rag_pipeline, prompt_builder, post_processor, cache, cost_ctrl)
    → EscalationChecker(config)
    → ProgressTracker()
    → DecisionEngine(chat_service, generate_service, rag_pipeline, session_mgr, checker, tracker)

STEP 6: Register Routes
    → router.include(chat_routes)
    → router.include(generate_routes)
    → router.include(hybrid_routes)
    → router.include(session_routes)
    → router.include(rag_routes)
    → router.include(health_routes)
    → app.include_router(router, prefix="/api/v1")

STEP 7: Ready
    → Log: "AI Agent Hybrid started on port {port}"
    → Swagger docs available at /docs
    → ReDoc available at /redoc

APPLICATION SHUTDOWN
─────────────────────
    → Close SQLite connections
    → Log: "AI Agent Hybrid shutdown"
```

### Hybrid Endpoint Flow

```
POST /api/v1/hybrid
    │
    ├─► Validate request body (Pydantic auto-validation)
    │   IF invalid: return 422 Validation Error
    │
    ├─► Get DecisionEngine from dependency injection
    │
    ├─► result = await decision_engine.route(
    │       session_id=request.session_id,
    │       message=request.message,
    │       options=request.options
    │   )
    │
    ├─► Convert RoutingResult → HybridResponse (API response model)
    │
    └─► Return HybridResponse (200 OK)

    ERROR CASES:
    ├─► SessionNotFoundError → 404
    ├─► OllamaConnectionError → 503
    ├─► GeminiTimeoutError → 504
    ├─► RateLimitError → 429
    ├─► LLMParseError → 500 (internal, tapi dengan pesan informatif)
    └─► Unhandled Exception → 500 generic
```

---

## 5. Data Structure

### 5.1 Unified API Response Model

```python
class HybridAPIResponse(BaseModel):
    """Response model untuk semua endpoint yang merespons client."""
    session_id: str
    type: Literal["chat", "generate"]
    message: str
    state: SessionState
    extracted_data: TORData | None = None
    tor_document: TORDocument | None = None
    escalation_info: EscalationInfo | None = None
    cached: bool = False
```

### 5.2 Health Check Response

```python
class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime_seconds: float
    components: dict[str, ComponentHealth]

class ComponentHealth(BaseModel):
    status: Literal["up", "down", "degraded"]
    details: dict | None = None
    latency_ms: float | None = None
```

### 5.3 Error Response

```python
class ErrorResponse(BaseModel):
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: str                    # E001 - E011
    message: str                 # human-readable message
    details: str | None = None   # technical details
    retry_after_seconds: int | None = None  # for rate limit errors
```

---

## 6. API Contract (Complete Endpoint List)

### 6.1 `POST /api/v1/hybrid` ⭐ (Main Endpoint)

**Deskripsi**: Endpoint utama. Kirim pesan, sistem otomatis routing.

| Aspect | Detail |
|---|---|
| Method | POST |
| Body | `HybridRequest` (session_id, message, options) |
| Response 200 | `HybridAPIResponse` |
| Response 404 | Session not found |
| Response 422 | Validation error |
| Response 429 | Gemini rate limit |
| Response 503 | Ollama down |
| Response 504 | Timeout |

---

### 6.2 `POST /api/v1/chat`

**Deskripsi**: Chat langsung dengan local LLM (tanpa auto-generate).

| Aspect | Detail |
|---|---|
| Method | POST |
| Body | `ChatRequest` (session_id, message) |
| Response 200 | `HybridAPIResponse` (type: "chat") |

---

### 6.3 `POST /api/v1/generate`

**Deskripsi**: Manual trigger Gemini.

| Aspect | Detail |
|---|---|
| Method | POST |
| Body | `GenerateRequest` (session_id, mode, force_regenerate) |
| Response 200 | `HybridAPIResponse` (type: "generate") |

---

### 6.4 `GET /api/v1/session/{session_id}`

**Deskripsi**: Get session state.

| Aspect | Detail |
|---|---|
| Method | GET |
| Path param | session_id (UUID) |
| Response 200 | Full session object + chat history |

---

### 6.5 `POST /api/v1/rag/ingest`

**Deskripsi**: Upload & ingest documents ke vector DB.

| Aspect | Detail |
|---|---|
| Method | POST |
| Body | multipart/form-data (files + category) |
| Response 200 | IngestResult |

---

### 6.6 `GET /api/v1/rag/status`

**Deskripsi**: Vector DB status & document list.

---

### 6.7 `GET /api/v1/health`

**Deskripsi**: System health check.

| Aspect | Detail |
|---|---|
| Response 200 | HealthResponse (all components up) |
| Response 503 | HealthResponse (critical component down) |

---

## 7. Dependencies

### Dependency ke modul lain

| Modul | Apa yang dipakai | Wajib? |
|---|---|---|
| **beta0.1.0 (Chat Engine)** | ChatService, SessionManager, OllamaProvider, semua models | ✅ |
| **beta0.1.1 (RAG)** | RAGPipeline | ❌ Opsional (graceful degradation) |
| **beta0.1.2 (Gemini Generator)** | GenerateService, GeminiProvider | ✅ |
| **beta0.1.3 (Decision Engine)** | DecisionEngine, EscalationChecker, ProgressTracker | ✅ |

### Library dependencies (complete `requirements.txt`)

```
# === Framework ===
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0
pydantic-settings>=2.0

# === AI Providers ===
ollama>=0.4.0
google-generativeai>=0.8.0

# === RAG ===
chromadb>=0.5.0
langchain-text-splitters>=0.3.0

# === Database ===
aiosqlite>=0.20.0

# === Utilities ===
python-dotenv>=1.0
python-multipart>=0.0.9
httpx>=0.27.0

# === Testing ===
pytest>=8.0
pytest-asyncio>=0.24.0

# === Optional: Frontend ===
# streamlit>=1.38.0
```

---

## 8. Pseudocode

### 8.1 FastAPI Application (`app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

from app.config import Settings
from app.api.router import api_router
from app.api.error_handlers import register_error_handlers
from app.dependencies import init_dependencies

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown."""
    start_time = time.time()
    settings = Settings()

    logger.info(f"Starting {settings.app_name} v{settings.app_version}...")

    # Init all dependencies
    deps = await init_dependencies(settings)
    app.state.deps = deps
    app.state.start_time = start_time
    app.state.settings = settings

    logger.info(
        f"{settings.app_name} ready on port {settings.app_port}. "
        f"Ollama: {settings.ollama_chat_model}, "
        f"Gemini: {settings.gemini_model}, "
        f"RAG: {'enabled' if deps.rag_pipeline else 'disabled'}"
    )

    yield  # Application is running

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")

app = FastAPI(
    title="AI Agent Hybrid — TOR Generator",
    description="Hybrid AI system combining local LLM (Ollama) and Google Gemini for professional TOR document generation.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
register_error_handlers(app)

# Routes
app.include_router(api_router, prefix="/api/v1")
```

### 8.2 Dependency Injection (`app/dependencies.py`)

```python
from dataclasses import dataclass

@dataclass
class AppDependencies:
    settings: Settings
    session_mgr: SessionManager
    ollama_provider: OllamaProvider
    gemini_provider: GeminiProvider
    rag_pipeline: RAGPipeline | None
    chat_service: ChatService
    generate_service: GenerateService
    decision_engine: DecisionEngine

async def init_dependencies(settings: Settings) -> AppDependencies:
    """Wire semua dependencies."""

    # Database
    db_path = settings.session_db_path
    await init_database(db_path)  # run migrations

    # Session Manager
    session_mgr = SessionManager(db_path)

    # Ollama Provider
    ollama = OllamaProvider(settings)

    # Gemini Provider
    gemini = GeminiProvider(settings)

    # RAG Pipeline (optional)
    rag_pipeline = None
    try:
        embedder = OllamaEmbedder(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        vector_store = ChromaVectorStore(persist_path=settings.vector_db_path)
        retriever = Retriever(vector_store, embedder,
                              default_top_k=settings.retrieval_top_k,
                              default_threshold=settings.similarity_threshold)
        rag_pipeline = RAGPipeline(
            loader=DocumentLoader(),
            chunker=TextChunker(),
            embedder=embedder,
            store=vector_store,
            retriever=retriever,
            formatter=ContextFormatter(),
        )
        logger.info(f"RAG pipeline initialized. Collection size: {vector_store.count()}")
    except Exception as e:
        logger.warning(f"RAG pipeline init failed, running without RAG: {e}")

    # Chat Service
    chat_service = ChatService(
        ollama=ollama,
        session_mgr=session_mgr,
        prompt_builder=PromptBuilder(),
        parser=ResponseParser(),
    )

    # Generate Service
    generate_service = GenerateService(
        gemini=gemini,
        session_mgr=session_mgr,
        rag_pipeline=rag_pipeline,
        prompt_builder=GeminiPromptBuilder(),
        post_processor=PostProcessor(),
        cache=TORCache(db_path),
        cost_ctrl=CostController(session_mgr, settings),
    )

    # Decision Engine
    escalation_config = EscalationConfig(
        max_idle_turns=settings.escalation_max_idle_turns,
        absolute_max_turns=settings.escalation_absolute_max_turns,
    )
    decision_engine = DecisionEngine(
        chat_service=chat_service,
        generate_service=generate_service,
        rag_pipeline=rag_pipeline,
        session_mgr=session_mgr,
        escalation_checker=EscalationChecker(escalation_config),
        progress_tracker=ProgressTracker(),
    )

    return AppDependencies(
        settings=settings,
        session_mgr=session_mgr,
        ollama_provider=ollama,
        gemini_provider=gemini,
        rag_pipeline=rag_pipeline,
        chat_service=chat_service,
        generate_service=generate_service,
        decision_engine=decision_engine,
    )

def get_deps(request) -> AppDependencies:
    """FastAPI dependency untuk inject ke route handlers."""
    return request.app.state.deps
```

### 8.3 Central Router (`app/api/router.py`)

```python
from fastapi import APIRouter

from app.api.routes import chat, generate, hybrid, session, rag, health

api_router = APIRouter()

api_router.include_router(hybrid.router, tags=["Hybrid"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(generate.router, tags=["Generate"])
api_router.include_router(session.router, tags=["Session"])
api_router.include_router(rag.router, tags=["RAG"])
api_router.include_router(health.router, tags=["Health"])
```

### 8.4 Hybrid Endpoint (`app/api/routes/hybrid.py`)

```python
from fastapi import APIRouter, Depends, Request

router = APIRouter()

@router.post("/hybrid", response_model=HybridAPIResponse)
async def hybrid_endpoint(
    request_body: HybridRequest,
    request: Request,
):
    """
    Main endpoint. Kirim pesan, sistem otomatis routing antara
    chat (local LLM) dan generate (Gemini).
    """
    deps = get_deps(request)

    result = await deps.decision_engine.route(
        session_id=request_body.session_id,
        message=request_body.message,
        options=request_body.options,
    )

    return _convert_to_api_response(result)


def _convert_to_api_response(result: RoutingResult) -> HybridAPIResponse:
    """Convert internal RoutingResult ke API response."""
    if result.generate_response:
        return HybridAPIResponse(
            session_id=result.session_id,
            type="generate",
            message=result.chat_response.message if result.chat_response
                    else "TOR berhasil dibuat.",
            state=_build_state(result),
            extracted_data=result.chat_response.extracted_data if result.chat_response else None,
            tor_document=result.generate_response.tor_document,
            escalation_info=result.escalation_info,
            cached=result.generate_response.cached,
        )
    else:
        return HybridAPIResponse(
            session_id=result.session_id,
            type="chat",
            message=result.chat_response.message,
            state=SessionState(
                status=result.chat_response.status,
                turn_count=result.chat_response.completeness_score,  # simplify
                completeness_score=result.chat_response.completeness_score,
                filled_fields=result.chat_response.extracted_data.filled_fields(),
                missing_fields=result.chat_response.missing_fields,
            ),
            extracted_data=result.chat_response.extracted_data,
        )
```

### 8.5 Health Endpoint (`app/api/routes/health.py`)

```python
from fastapi import APIRouter, Request
import time

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    deps = get_deps(request)
    components = {}
    overall = "healthy"

    # Check Ollama
    try:
        start = time.monotonic()
        await deps.ollama_provider.client.list()
        latency = (time.monotonic() - start) * 1000
        components["ollama"] = ComponentHealth(
            status="up",
            details={"model": deps.settings.ollama_chat_model},
            latency_ms=round(latency, 1),
        )
    except Exception as e:
        components["ollama"] = ComponentHealth(status="down", details={"error": str(e)})
        overall = "degraded"

    # Check Gemini
    try:
        components["gemini"] = ComponentHealth(
            status="up",
            details={"model": deps.settings.gemini_model},
        )
    except Exception:
        components["gemini"] = ComponentHealth(status="down")
        overall = "degraded"

    # Check RAG
    if deps.rag_pipeline:
        try:
            status = await deps.rag_pipeline.get_status()
            components["rag"] = ComponentHealth(
                status="up",
                details={"chunks": status["vector_db"]["total_chunks"]},
            )
        except Exception:
            components["rag"] = ComponentHealth(status="down")
    else:
        components["rag"] = ComponentHealth(status="degraded", details={"reason": "not initialized"})

    # Check SQLite
    try:
        components["database"] = ComponentHealth(status="up", details={"type": "sqlite"})
    except Exception:
        components["database"] = ComponentHealth(status="down")
        overall = "unhealthy"

    return HealthResponse(
        status=overall,
        version=deps.settings.app_version,
        uptime_seconds=round(time.time() - request.app.state.start_time, 1),
        components=components,
    )
```

### 8.6 Global Error Handler (`app/api/error_handlers.py`)

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_error_handlers(app: FastAPI):
    @app.exception_handler(SessionNotFoundError)
    async def session_not_found(request: Request, exc: SessionNotFoundError):
        return JSONResponse(status_code=404, content={
            "error": {"code": "E006", "message": str(exc)}
        })

    @app.exception_handler(OllamaConnectionError)
    async def ollama_down(request: Request, exc: OllamaConnectionError):
        return JSONResponse(status_code=503, content={
            "error": {"code": "E001", "message": str(exc)}
        })

    @app.exception_handler(OllamaTimeoutError)
    async def ollama_timeout(request: Request, exc: OllamaTimeoutError):
        return JSONResponse(status_code=504, content={
            "error": {"code": "E008", "message": str(exc)}
        })

    @app.exception_handler(GeminiTimeoutError)
    async def gemini_timeout(request: Request, exc: GeminiTimeoutError):
        return JSONResponse(status_code=504, content={
            "error": {"code": "E008", "message": str(exc)}
        })

    @app.exception_handler(RateLimitError)
    async def rate_limit(request: Request, exc: RateLimitError):
        return JSONResponse(status_code=429, content={
            "error": {
                "code": "E003",
                "message": str(exc),
                "retry_after_seconds": 60
            }
        })

    @app.exception_handler(LLMParseError)
    async def llm_parse(request: Request, exc: LLMParseError):
        return JSONResponse(status_code=500, content={
            "error": {"code": "E002", "message": str(exc)}
        })

    @app.exception_handler(Exception)
    async def generic_error(request: Request, exc: Exception):
        logger.exception(f"Unhandled error: {exc}")
        return JSONResponse(status_code=500, content={
            "error": {
                "code": "E999",
                "message": "Internal server error. Silakan coba lagi.",
                "details": str(exc) if settings.app_env == "development" else None,
            }
        })
```

### 8.7 Database Init (`app/db/database.py`)

```python
import aiosqlite
from pathlib import Path

MIGRATION_DIR = Path(__file__).parent / "migrations"

async def init_database(db_path: str):
    """Initialize database dan run semua migration."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Enable WAL mode untuk concurrent access
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        # Run migration files in order
        migration_files = sorted(MIGRATION_DIR.glob("*.sql"))
        for migration in migration_files:
            sql = migration.read_text(encoding="utf-8")
            await db.executescript(sql)
            logger.info(f"Migration applied: {migration.name}")

        await db.commit()
```

---

## 9. Edge Cases

### Edge Case 1: Ollama Belum Start saat App Startup

**Trigger**: `ollama serve` belum dijalankan.

**Handling**:
```python
# Di init_dependencies:
try:
    await ollama.client.list()
    logger.info("Ollama connected")
except Exception as e:
    logger.error(f"Ollama not available: {e}")
    # App TETAP start tapi health check akan report "down"
    # Chat endpoint akan return 503 saat dipanggil
```

### Edge Case 2: `.env` Tidak Ada atau GEMINI_API_KEY Kosong

**Trigger**: User lupa setup `.env`.

**Handling**:
```python
class Settings(BaseSettings):
    gemini_api_key: str   # required, akan error saat startup jika kosong

    class Config:
        env_file = ".env"

# Startup akan gagal dengan pesan jelas:
# pydantic_core._pydantic_core.ValidationError:
# 1 validation error for Settings
# gemini_api_key: field required
```

### Edge Case 3: Port 8000 Sudah Dipakai

**Trigger**: Service lain di port 8000.

**Handling**: Uvicorn akan error `[Errno 10048] Address already in use`. User bisa ubah di `.env`: `APP_PORT=8001`.

### Edge Case 4: SQLite Database Locked

**Trigger**: Multiple concurrent requests meng-write bersamaan.

**Handling**: WAL mode + aiosqlite menangani ini secara native. Jika tetap locked:
```python
# Set busy_timeout agar SQLite retry otomatis
await db.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
```

### Edge Case 5: Request Body Terlalu Besar

**Trigger**: User kirim message >5000 karakter atau upload file >1MB.

**Handling**: Pydantic validation `max_length=5000` untuk message. Untuk file upload, FastAPI middleware:
```python
# Di upload handler:
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB
for file in files:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File {file.filename} terlalu besar (max 1MB)")
```

---

## 10. File yang Harus Dibuat

```
app/
├── main.py                         # FastAPI application + lifespan
├── config.py                       # Pydantic Settings (SUDAH ADA dari beta0.1.0, update)
├── dependencies.py                 # Dependency injection wiring
│
├── api/
│   ├── __init__.py
│   ├── router.py                   # Central router
│   ├── error_handlers.py           # Global exception handlers
│   └── routes/
│       ├── __init__.py
│       ├── hybrid.py               # POST /api/v1/hybrid ⭐
│       └── health.py               # GET /api/v1/health (UPDATE dari beta0.1.0)
│
├── db/
│   └── database.py                 # init_database() + migration runner
│
├── utils/
│   ├── logger.py                   # Logging setup
│   └── errors.py                   # Custom exception classes (UPDATE: consolidate all)
│
# Root files
├── .env.example                    # Template .env
├── .gitignore                      # Python gitignore
├── requirements.txt                # All dependencies
├── Makefile                        # Dev shortcuts
└── README.md                       # Setup & usage guide
```

### `.env.example`

```bash
# === APP ===
APP_NAME=ai-agent-hybrid
APP_VERSION=0.1.0
APP_PORT=8000
APP_ENV=development
LOG_LEVEL=INFO

# === OLLAMA ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=qwen2.5:7b-instruct
OLLAMA_EMBED_MODEL=bge-m3
OLLAMA_TIMEOUT_SECONDS=60
OLLAMA_TEMPERATURE=0.3
OLLAMA_NUM_CTX=4096

# === GEMINI ===
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=4096
GEMINI_TIMEOUT_SECONDS=120

# === RAG ===
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=bge-m3
CHUNK_SIZE=500
CHUNK_OVERLAP=50
RETRIEVAL_TOP_K=3
SIMILARITY_THRESHOLD=0.7

# === SESSION ===
SESSION_DB_PATH=./data/sessions.db
SESSION_EXPIRY_HOURS=24

# === COST CONTROL ===
MAX_GEMINI_CALLS_PER_SESSION=3
MAX_GEMINI_CALLS_PER_HOUR=20
MAX_CHAT_TURNS_PER_SESSION=15

# === ESCALATION ===
ESCALATION_MAX_IDLE_TURNS=5
ESCALATION_ABSOLUTE_MAX_TURNS=10
```

### `Makefile`

```makefile
.PHONY: run test ingest setup

# Run development server
run:
	uvicorn app.main:app --reload --port 8000

# Run tests
test:
	pytest tests/ -v

# Ingest example TOR documents
ingest:
	python scripts/ingest_documents.py --dir data/documents/ --category tor_example

# First-time setup
setup:
	pip install -r requirements.txt
	ollama pull qwen2.5:7b-instruct
	ollama pull bge-m3
	cp .env.example .env
	@echo "Edit .env dan set GEMINI_API_KEY sebelum make run"

# Health check
health:
	curl -s http://localhost:8000/api/v1/health | python -m json.tool
```

---

## 11. Cara Test Full System End-to-End

```bash
# 1. Setup (pertama kali)
make setup
# Edit .env → set GEMINI_API_KEY

# 2. Start Ollama
ollama serve

# 3. Start server
make run

# 4. Health check
make health

# 5. (Optional) Ingest sample TOR documents
make ingest

# 6. Test hybrid flow: conversation baru
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "Saya ingin buat TOR untuk workshop AI di kantor pemerintah"}'

# 7. Continue conversation (pakai session_id dari response)
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "message": "3 hari, 30 peserta, budget 50 juta, bulan Juli 2026"
  }'

# 8. Test escalation: lazy user
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"message": "buat TOR AI"}'

# (lanjut dengan session_id)
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "message": "terserah aja"}'

# 9. Force generate
curl -X POST http://localhost:8000/api/v1/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SESSION_ID",
    "options": {"force_generate": true}
  }'

# 10. Check Swagger docs
# Open browser: http://localhost:8000/docs
```
