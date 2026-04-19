from fastapi import APIRouter

from app.api.routes import health, chat, session, rag, generate, hybrid, generate_doc, models

api_router = APIRouter()

api_router.include_router(hybrid.router, tags=["Hybrid"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(generate.router, tags=["Generate"])
api_router.include_router(generate_doc.router, tags=["Generate-Document"])
api_router.include_router(models.router, tags=["Models"])
api_router.include_router(session.router, tags=["Session"])
api_router.include_router(rag.router, tags=["RAG"])
api_router.include_router(health.router, tags=["Health"])
