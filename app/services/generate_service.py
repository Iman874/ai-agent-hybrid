import logging
import asyncio
import time

from app.ai.base_generator import BaseGeneratorProvider
from app.core.session_manager import SessionManager
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history as gemini_format_history
from app.core.ollama_prompt_builder import OllamaPromptBuilder, format_chat_history as ollama_format_history
from app.core.post_processor import PostProcessor
from app.core.cost_controller import CostController
from app.db.repositories.cache_repo import TORCache
from app.rag.pipeline import RAGPipeline
from app.core.style_manager import StyleManager
from app.models.generate import (
    TORDocument, TORMetadata, GenerateResult, GeminiResponse
)
from app.models.tor import TORData
from app.utils.errors import (
    GeminiTimeoutError, GeminiAPIError,
    OllamaConnectionError, OllamaTimeoutError, NoProviderAvailableError,
)

logger = logging.getLogger("ai-agent-hybrid.generate")


class GenerateService:
    """Orchestrator utama untuk TOR generation — multi-provider.

    Mendukung Gemini (cloud) dan Ollama (local) sebagai generator TOR.
    Routing provider berdasarkan mode: "auto", "gemini", atau "ollama".
    """

    def __init__(
        self,
        gemini_provider: BaseGeneratorProvider,
        ollama_provider: BaseGeneratorProvider,
        session_mgr: SessionManager,
        rag_pipeline: RAGPipeline | None,
        gemini_prompt_builder: GeminiPromptBuilder,
        ollama_prompt_builder: OllamaPromptBuilder,
        post_processor: PostProcessor,
        cache: TORCache,
        cost_ctrl: CostController,
        style_manager: StyleManager,
    ):
        self.providers = {
            "gemini": gemini_provider,
            "ollama": ollama_provider,
        }
        self.prompt_builders = {
            "gemini": gemini_prompt_builder,
            "ollama": ollama_prompt_builder,
        }
        self.session_mgr = session_mgr
        self.rag = rag_pipeline
        self.post_processor = post_processor
        self.cache = cache
        self.cost_ctrl = cost_ctrl
        self.style_manager = style_manager

        # Threshold untuk auto mode
        self.auto_threshold = 0.8

    async def generate_tor(
        self,
        session_id: str,
        mode: str = "standard",
        generator: str = "auto",
        data_override: TORData | None = None,
        force_regenerate: bool = False,
    ) -> GenerateResult:
        """Full generate pipeline — multi-provider.

        Args:
            session_id: ID session chat.
            mode: "standard" (data lengkap) atau "escalation" (data parsial).
            generator: "auto" | "gemini" | "ollama".
            data_override: Data TOR override (optional).
            force_regenerate: Bypass cache.

        Returns:
            GenerateResult dengan TOR document.

        Raises:
            NoProviderAvailableError: Semua provider tidak tersedia.
            InsufficientDataError: Data belum cukup (standard mode).
        """
        logger.info(
            f"Generate TOR: session={session_id}, mode={mode}, generator={generator}"
        )

        # Step 1: Tentukan provider
        provider_name = await self._resolve_provider(session_id, generator, mode)
        provider = self.providers[provider_name]
        prompt_builder = self.prompt_builders[provider_name]
        logger.info(f"Using provider: {provider_name} ({provider.provider_name})")

        # Step 2: Cost check (hanya untuk Gemini)
        if provider_name == "gemini":
            await self.cost_ctrl.check(session_id)

        # Step 3: Check cache (Gemini standard mode only)
        if (
            not force_regenerate
            and provider_name == "gemini"
            and mode == "standard"
        ):
            cached = await self.cache.get(session_id)
            if cached:
                logger.info(f"Serving TOR from cache: session={session_id}")
                return GenerateResult(
                    session_id=session_id, tor_document=cached, cached=True
                )

        # Step 4: Get session data
        session = await self.session_mgr.get(session_id)
        data = data_override or session.extracted_data

        # Note: Completeness threshold is not enforced for generation.

        history = await self.session_mgr.get_chat_history(session_id)

        # Step 5: Get RAG examples (optional)
        rag_examples = None
        if self.rag and data.judul:
            try:
                rag_examples = await self.rag.retrieve(data.judul, top_k=2)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        # Step 5b: Get active formatting style
        active_style = self.style_manager.get_active_style()
        format_spec = active_style.to_prompt_spec()

        # Step 6: Build prompt (pilih builder sesuai provider)
        if mode == "standard":
            prompt = prompt_builder.build_standard(
                data=data,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )
        else:
            if provider_name == "gemini":
                formatted_history = gemini_format_history(history)
            else:
                formatted_history = ollama_format_history(history)

            prompt = prompt_builder.build_escalation(
                chat_history=formatted_history,
                partial_data=data,
                rag_examples=rag_examples,
                format_spec=format_spec,
            )

        # Step 7: Call provider
        start_time = time.monotonic()

        if provider_name == "gemini":
            gemini_response = await self._call_gemini_with_retry(
                prompt, session_id, mode, retries=3, backoff=[2, 5, 10]
            )
            raw_text = gemini_response.text
            duration_ms = gemini_response.duration_ms
            prompt_tokens = gemini_response.prompt_tokens
            completion_tokens = gemini_response.completion_tokens
        else:
            # Ollama — cukup sekali panggil (lebih stabil)
            raw_text = await self._call_ollama(prompt, session_id, mode)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            prompt_tokens = 0
            completion_tokens = 0

        # Step 8: Post-process
        processed = self.post_processor.process(raw_text, style=active_style)

        # Step 9: Build TOR document
        model_name = (
            provider.model_name
            if hasattr(provider, "model_name")
            else provider.model
        )
        tor_doc = TORDocument(
            content=processed.content,
            metadata=TORMetadata(
                generated_by=model_name,
                generator=provider_name,
                mode=mode,
                word_count=processed.word_count,
                generation_time_ms=duration_ms,
                has_assumptions=processed.has_assumptions,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
        )

        # Step 10: Cache & update session
        # Cache untuk semua provider (agar export bisa bekerja)
        await self.cache.store(session_id, tor_doc)
        if provider_name == "gemini":
            await self.cost_ctrl.log_call(
                session_id, model_name, mode,
                prompt_tokens, completion_tokens,
                duration_ms, success=True,
            )

        await self.session_mgr.update(
            session_id,
            state="COMPLETED",
            generated_tor=processed.content,
            gemini_calls_count=(
                session.gemini_calls_count + 1
                if provider_name == "gemini"
                else session.gemini_calls_count
            ),
            total_tokens_gemini=(
                session.total_tokens_gemini + prompt_tokens + completion_tokens
                if provider_name == "gemini"
                else session.total_tokens_gemini
            ),
        )

        logger.info(
            f"TOR generated: session={session_id}, mode={mode}, "
            f"generator={provider_name}, words={processed.word_count}, "
            f"time={duration_ms}ms"
        )
        return GenerateResult(
            session_id=session_id, tor_document=tor_doc, cached=False
        )

    async def _resolve_provider(
        self, session_id: str, generator: str, mode: str
    ) -> str:
        """Tentukan provider mana yang dipakai berdasarkan mode.

        Args:
            session_id: ID session untuk cek completeness.
            generator: "auto" | "gemini" | "ollama".
            mode: "standard" | "escalation".

        Returns:
            str: Nama provider terpilih ("gemini" | "ollama").

        Raises:
            NoProviderAvailableError: Semua provider tidak tersedia.
        """
        if generator == "gemini":
            if await self.providers["gemini"].is_available():
                return "gemini"
            elif await self.providers["ollama"].is_available():
                logger.warning("Gemini unavailable, falling back to Ollama")
                return "ollama"
            else:
                raise NoProviderAvailableError(
                    "Gemini unavailable (API key missing or invalid), "
                    "Ollama unavailable (not running or model not found)"
                )

        elif generator == "ollama":
            if await self.providers["ollama"].is_available():
                return "ollama"
            elif await self.providers["gemini"].is_available():
                logger.warning("Ollama unavailable, falling back to Gemini")
                return "gemini"
            else:
                raise NoProviderAvailableError(
                    "Ollama unavailable (not running or model not found), "
                    "Gemini unavailable (API key missing or invalid)"
                )

        else:  # "auto"
            session = await self.session_mgr.get(session_id)
            # Jika completeness tinggi → Ollama (local, gratis)
            # Jika completeness rendah → Gemini (butuh escalation)
            if session.completeness_score >= self.auto_threshold:
                if await self.providers["ollama"].is_available():
                    return "ollama"
                elif await self.providers["gemini"].is_available():
                    return "gemini"
            else:
                if await self.providers["gemini"].is_available():
                    return "gemini"
                elif await self.providers["ollama"].is_available():
                    return "ollama"

            raise NoProviderAvailableError(
                "No generator provider available. "
                "Ensure Ollama is running or Gemini API key is configured."
            )

    async def _call_gemini_with_retry(
        self, prompt: str, session_id: str, mode: str,
        retries: int = 3, backoff: list[int] = [2, 5, 10]
    ) -> GeminiResponse:
        """Call Gemini with retry and backoff."""
        last_error = None
        for attempt in range(retries):
            try:
                return await self.providers["gemini"].generate(prompt)
            except (GeminiTimeoutError, GeminiAPIError, Exception) as e:
                last_error = e
                logger.warning(
                    f"Gemini attempt {attempt + 1}/{retries} failed: {e}"
                )
                await self.cost_ctrl.log_call(
                    session_id, self.providers["gemini"].model_name, mode,
                    0, 0, 0, success=False, error_msg=str(e)[:200]
                )
                if attempt < retries - 1:
                    await asyncio.sleep(backoff[attempt])

        raise last_error

    async def _call_ollama(
        self, prompt: str, session_id: str, mode: str
    ) -> str:
        """Call Ollama untuk generate TOR — single attempt.

        Ollama lokal lebih stabil, retry tidak terlalu diperlukan.
        Jika gagal, error akan di-handle oleh caller.
        """
        try:
            return await self.providers["ollama"].generate(prompt)
        except (OllamaConnectionError, OllamaTimeoutError) as e:
            logger.error(f"Ollama generate failed: session={session_id}, error={e}")
            raise
