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
