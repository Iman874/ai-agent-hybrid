import logging
from fastapi import APIRouter, Request

from app.core.capability_resolver import ModelCapabilityResolver

logger = logging.getLogger("ai-agent-hybrid.api.models")

router = APIRouter()

_resolver = ModelCapabilityResolver()


@router.get("/models")
async def list_models(request: Request):
    """Return daftar model yang tersedia untuk chat, termasuk capabilities."""
    settings = request.app.state.settings
    models = []

    # Check Ollama availability
    try:
        import ollama as ollama_lib
        client = ollama_lib.AsyncClient(host=settings.ollama_base_url)
        result = await client.list()
        for m in result.models:
            caps = _resolver.resolve(m.model, "ollama")
            models.append({
                "id": m.model,
                "type": "local",
                "provider": "ollama",
                "status": "available",
                "capabilities": {
                    "supports_text": caps.supports_text,
                    "supports_image_input": caps.supports_image_input,
                    "supports_streaming": caps.supports_streaming,
                },
            })
    except Exception as e:
        logger.warning(f"Ollama not available: {e}")
        caps = _resolver.resolve(settings.ollama_chat_model, "ollama")
        models.append({
            "id": settings.ollama_chat_model,
            "type": "local",
            "provider": "ollama",
            "status": "offline",
            "capabilities": {
                "supports_text": caps.supports_text,
                "supports_image_input": caps.supports_image_input,
                "supports_streaming": caps.supports_streaming,
            },
        })

    # Gemini — always available if API key set
    if settings.gemini_api_key:
        caps = _resolver.resolve(settings.gemini_model, "google")
        models.append({
            "id": settings.gemini_model,
            "type": "gemini",
            "provider": "google",
            "status": "available",
            "capabilities": {
                "supports_text": caps.supports_text,
                "supports_image_input": caps.supports_image_input,
                "supports_streaming": caps.supports_streaming,
            },
        })

    return {"models": models, "default_chat_mode": "local"}
