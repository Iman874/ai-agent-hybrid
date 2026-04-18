import logging
import time
import aiosqlite
from fastapi import APIRouter, Request
from app.models.api import HealthResponse, ComponentHealth

logger = logging.getLogger("ai-agent-hybrid.api.health")

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Full system health check with component status."""
    settings = request.app.state.settings
    components = {}
    overall = "healthy"

    # Check Ollama
    try:
        start = time.monotonic()
        ollama = request.app.state.chat_service.ollama
        await ollama.client.list()
        latency = (time.monotonic() - start) * 1000
        components["ollama"] = ComponentHealth(
            status="up",
            details={"model": settings.ollama_chat_model},
            latency_ms=round(latency, 1),
        )
    except Exception as e:
        components["ollama"] = ComponentHealth(
            status="down", details={"error": str(e)[:100]}
        )
        overall = "degraded"

    # Check Gemini
    if settings.gemini_api_key and settings.gemini_api_key != "your-api-key-here":
        components["gemini"] = ComponentHealth(
            status="up",
            details={"model": settings.gemini_model},
        )
    else:
        components["gemini"] = ComponentHealth(
            status="degraded",
            details={"reason": "API key not configured"},
        )
        overall = "degraded"

    # Check RAG
    rag = getattr(request.app.state, "rag_pipeline", None)
    if rag:
        try:
            status = await rag.get_status()
            components["rag"] = ComponentHealth(
                status="up",
                details={"chunks": status.get("vector_db", {}).get("total_chunks", 0)},
            )
        except Exception:
            components["rag"] = ComponentHealth(status="down")
    else:
        components["rag"] = ComponentHealth(
            status="degraded", details={"reason": "not initialized"}
        )

    # Check Database
    try:
        async with aiosqlite.connect(settings.session_db_path) as db:
            await db.execute("SELECT 1")
        components["database"] = ComponentHealth(
            status="up", details={"type": "sqlite"}
        )
    except Exception as e:
        components["database"] = ComponentHealth(
            status="down", details={"error": str(e)[:100]}
        )
        overall = "unhealthy"

    uptime = time.time() - getattr(request.app.state, "start_time", time.time())

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        uptime_seconds=round(uptime, 1),
        components=components,
    )
