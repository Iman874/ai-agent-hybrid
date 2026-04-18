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
