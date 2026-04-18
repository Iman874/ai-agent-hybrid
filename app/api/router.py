from fastapi import APIRouter

from app.api.routes import health, chat, session, rag

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(session.router, tags=["Session"])
api_router.include_router(rag.router, tags=["RAG"])

