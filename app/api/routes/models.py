import logging
from fastapi import APIRouter, Request

logger = logging.getLogger("ai-agent-hybrid.api.models")

router = APIRouter()


@router.get("/models")
async def list_models(request: Request):
    """Return daftar model yang tersedia untuk chat."""
    settings = request.app.state.settings
    models = []

    # Check Ollama availability
    try:
        import ollama as ollama_lib
        client = ollama_lib.AsyncClient(host=settings.ollama_base_url)
        result = await client.list()
        for m in result.models:
            models.append({
                "id": m.model,
                "type": "local",
                "provider": "ollama",
                "status": "available",
            })
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        models.append({
            "id": settings.ollama_chat_model,
            "type": "local",
            "provider": "ollama",
            "status": "offline",
        })

    # Gemini — always available if API key set
    if settings.gemini_api_key:
        models.append({
            "id": settings.gemini_model,
            "type": "gemini",
            "provider": "google",
            "status": "available",
        })

    return {"models": models, "default_chat_mode": "local"}
