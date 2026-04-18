# Task 05 — Error Handlers: Refactor ke Modular Function

## 1. Judul Task

Refactor global error handlers di `app/main.py` ke `app/api/error_handlers.py` — satu function `register_error_handlers(app)` yang mendaftarkan semua exception handlers.

## 2. Deskripsi

Saat ini error handlers didefinisikan inline di `app/main.py`. Refactor ke file terpisah agar `main.py` lebih clean dan handler bisa di-test secara independen. Tambahkan handler untuk `GeminiAPIError` dan `InsufficientDataError`.

## 3. Tujuan Teknis

- `register_error_handlers(app)` — satu function yang mendaftarkan semua handlers
- Maintain semua existing handlers (404, 503, 504, 500)
- Tambah: `GeminiAPIError` → 502, `InsufficientDataError` → 400, `RateLimitError` → 429
- Development mode: include error details di response

## 4. Scope

### Yang dikerjakan
- `app/api/error_handlers.py` — semua error handlers
- Update `app/main.py` — remove inline handlers, call `register_error_handlers(app)`

### Yang tidak dikerjakan
- Custom middleware
- Request logging middleware

## 5. Langkah Implementasi

### Step 1: Buat `app/api/error_handlers.py`

```python
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.errors import (
    SessionNotFoundError, OllamaConnectionError, OllamaTimeoutError,
    GeminiTimeoutError, GeminiAPIError, RateLimitError,
    LLMParseError, InsufficientDataError,
)

logger = logging.getLogger("ai-agent-hybrid.errors")


def register_error_handlers(app: FastAPI):
    """Register semua global exception handlers."""

    @app.exception_handler(SessionNotFoundError)
    async def handle_session_not_found(request: Request, exc: SessionNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(InsufficientDataError)
    async def handle_insufficient_data(request: Request, exc: InsufficientDataError):
        return JSONResponse(
            status_code=400,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(RateLimitError)
    async def handle_rate_limit(request: Request, exc: RateLimitError):
        return JSONResponse(
            status_code=429,
            content={"error": {"code": exc.code, "message": exc.message, "retry_after_seconds": 60}},
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

    @app.exception_handler(GeminiTimeoutError)
    async def handle_gemini_timeout(request: Request, exc: GeminiTimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(GeminiAPIError)
    async def handle_gemini_api(request: Request, exc: GeminiAPIError):
        return JSONResponse(
            status_code=502,
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
```

### Step 2: Update `app/main.py`

- Remove semua inline `@app.exception_handler(...)` blocks
- Tambah `from app.api.error_handlers import register_error_handlers`
- Tambah `register_error_handlers(app)` sebelum routes

### Step 3: Verifikasi

Server start tanpa error. Health check masih return 200.

## 6. Output yang Diharapkan

Error handlers terpusat di satu file. `app/main.py` lebih clean.

## 7. Dependencies

- Semua custom exceptions sudah ada di `app/utils/errors.py`

## 8. Acceptance Criteria

- [ ] `app/api/error_handlers.py` berisi semua handlers
- [ ] `app/main.py` tidak punya inline error handlers
- [ ] Semua error code ter-map: 400, 404, 429, 502, 503, 504, 500
- [ ] Server berjalan tanpa error

## 9. Estimasi

**Low** — ~45 menit
