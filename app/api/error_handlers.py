import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.errors import (
    SessionNotFoundError,
    OllamaConnectionError,
    OllamaTimeoutError,
    GeminiTimeoutError,
    GeminiAPIError,
    RateLimitError,
    LLMParseError,
    InsufficientDataError,
    DocumentParseError,
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

    @app.exception_handler(DocumentParseError)
    async def handle_document_parse(request: Request, exc: DocumentParseError):
        return JSONResponse(
            status_code=400,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(Exception)
    async def handle_generic(request: Request, exc: Exception):
        import traceback
        tb = traceback.format_exc()
        logger.exception(f"Unhandled error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "E999", "message": "Internal server error.", "details": tb}},
        )
