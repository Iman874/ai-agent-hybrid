import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.api.router import api_router
from app.api.error_handlers import register_error_handlers
from app.db.database import init_db
from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.services.chat_service import ChatService
from app.utils.logger import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown."""
    settings = Settings()
    app.state.settings = settings
    app.state.start_time = time.time()

    logger.info(f"Starting {settings.app_name}...")

    # Init database
    await init_db(settings.session_db_path)
    logger.info("Database initialized")

    # Init services
    ollama_provider = OllamaProvider(settings)
    session_mgr = SessionManager(settings.session_db_path)
    app.state.session_mgr = session_mgr  # expose untuk route session list

    from app.rag.pipeline import RAGPipeline
    # Init RAG Pipeline
    rag_pipeline = RAGPipeline(settings)
    app.state.rag_pipeline = rag_pipeline
    logger.info("RAG Pipeline initialized")

    from app.ai.gemini_provider import GeminiProvider
    from app.ai.gemini_chat_provider import GeminiChatProvider
    from app.core.gemini_prompt_builder import GeminiPromptBuilder
    from app.core.post_processor import PostProcessor
    from app.core.cost_controller import CostController
    from app.core.style_extractor import StyleExtractor
    from app.core.style_manager import StyleManager
    from app.db.repositories.cache_repo import TORCache
    from app.db.repositories.doc_generation_repo import DocGenerationRepo
    from app.services.generate_service import GenerateService

    # Init Gemini Generator components
    gemini_provider = GeminiProvider(settings)
    tor_cache = TORCache(settings.session_db_path)
    cost_controller = CostController(session_mgr, settings)
    
    app.state.doc_gen_repo = DocGenerationRepo(settings.session_db_path)

    post_processor = PostProcessor()

    app.state.gemini_provider = gemini_provider
    app.state.post_processor = post_processor
    app.state.style_extractor = StyleExtractor(gemini_provider)
    
    style_manager = StyleManager(settings.tor_styles_dir if hasattr(settings, 'tor_styles_dir') else "data/tor_styles")
    app.state.style_manager = style_manager

    app.state.generate_service = GenerateService(
        gemini=gemini_provider,
        session_mgr=session_mgr,
        rag_pipeline=rag_pipeline,
        prompt_builder=GeminiPromptBuilder(),
        post_processor=PostProcessor(),
        cache=tor_cache,
        cost_ctrl=cost_controller,
        style_manager=style_manager,
    )
    logger.info("Generate Service initialized")

    # Expose tor_cache untuk route export
    app.state.tor_cache = tor_cache

    # Init Document Exporter
    from app.services.document_exporter import DocumentExporterService
    app.state.document_exporter = DocumentExporterService()
    logger.info("Document Exporter Service initialized")

    # Init Gemini Chat Provider (for chat mode)
    gemini_chat_provider = GeminiChatProvider(settings)
    app.state.gemini_chat_provider = gemini_chat_provider
    logger.info("Gemini Chat Provider initialized")

    app.state.chat_service = ChatService(
        ollama=ollama_provider,
        session_mgr=session_mgr,
        prompt_builder=PromptBuilder(),
        parser=ResponseParser(),
        rag_pipeline=rag_pipeline,
        gemini_chat=gemini_chat_provider,
    )

    from app.core.escalation_config import EscalationConfig
    from app.core.escalation_checker import EscalationChecker
    from app.core.progress_tracker import ProgressTracker
    from app.core.decision_engine import DecisionEngine
    from app.db.repositories.escalation_repo import EscalationLogger

    # Init Decision Engine components
    escalation_checker = EscalationChecker(EscalationConfig(
        max_idle_turns=settings.escalation_max_idle_turns,
        absolute_max_turns=settings.escalation_absolute_max_turns,
    ))
    progress_tracker = ProgressTracker()
    escalation_logger = EscalationLogger(settings.session_db_path)

    app.state.decision_engine = DecisionEngine(
        chat_service=app.state.chat_service,
        generate_service=app.state.generate_service,
        session_mgr=session_mgr,
        escalation_checker=escalation_checker,
        progress_tracker=progress_tracker,
        escalation_logger=escalation_logger,
        rag_pipeline=rag_pipeline,
    )
    logger.info("Decision Engine initialized")

    logger.info(
        f"{settings.app_name} ready! "
        f"Model: {settings.ollama_chat_model}, "
        f"DB: {settings.session_db_path}"
    )

    yield  # App is running

    logger.info(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title="AI Agent Hybrid — TOR Generator",
    description="Hybrid AI system combining local LLM (Ollama) and Google Gemini for professional TOR document generation.",
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

# === Error Handlers ===
register_error_handlers(app)

# === Routes ===
app.include_router(api_router, prefix="/api/v1")

from app.api.routes.ws_chat import router as ws_router
app.include_router(ws_router)






