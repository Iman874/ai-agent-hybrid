import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings
from app.api.router import api_router
from app.db.database import init_db
from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.services.chat_service import ChatService
from app.utils.errors import (
    AppError,
    OllamaConnectionError,
    OllamaTimeoutError,
    SessionNotFoundError,
    LLMParseError,
)
from app.utils.logger import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown."""
    settings = Settings()
    app.state.settings = settings

    logger.info(f"Starting {settings.app_name}...")

    # Init database
    await init_db(settings.session_db_path)
    logger.info("Database initialized")

    # Init services
    ollama_provider = OllamaProvider(settings)
    session_mgr = SessionManager(settings.session_db_path)

    from app.rag.pipeline import RAGPipeline
    # Init RAG Pipeline
    rag_pipeline = RAGPipeline(settings)
    app.state.rag_pipeline = rag_pipeline
    logger.info("RAG Pipeline initialized")

    from app.ai.gemini_provider import GeminiProvider
    from app.core.gemini_prompt_builder import GeminiPromptBuilder
    from app.core.post_processor import PostProcessor
    from app.core.cost_controller import CostController
    from app.db.repositories.cache_repo import TORCache
    from app.services.generate_service import GenerateService

    # Init Gemini Generator components
    gemini_provider = GeminiProvider(settings)
    tor_cache = TORCache(settings.session_db_path)
    cost_controller = CostController(session_mgr, settings)

    app.state.generate_service = GenerateService(
        gemini=gemini_provider,
        session_mgr=session_mgr,
        rag_pipeline=rag_pipeline,
        prompt_builder=GeminiPromptBuilder(),
        post_processor=PostProcessor(),
        cache=tor_cache,
        cost_ctrl=cost_controller,
    )
    logger.info("Generate Service initialized")

    app.state.chat_service = ChatService(
        ollama=ollama_provider,
        session_mgr=session_mgr,
        prompt_builder=PromptBuilder(),
        parser=ResponseParser(),
        rag_pipeline=rag_pipeline,
    )

    logger.info(
        f"{settings.app_name} ready! "
        f"Model: {settings.ollama_chat_model}, "
        f"DB: {settings.session_db_path}"
    )

    yield  # App is running

    logger.info(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title="AI Agent Hybrid — Chat Engine",
    description="Local LLM interviewer for TOR data collection.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Global Error Handlers ===

@app.exception_handler(SessionNotFoundError)
async def handle_session_not_found(request: Request, exc: SessionNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": exc.code, "message": exc.message, "session_id": exc.session_id}},
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

# === Routes ===
app.include_router(api_router, prefix="/api/v1")
