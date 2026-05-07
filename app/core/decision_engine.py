import logging
import aiosqlite

from app.services.chat_service import ChatService, ChatResult
from app.services.generate_service import GenerateService
from app.core.session_manager import SessionManager
from app.core.escalation_checker import EscalationChecker
from app.core.progress_tracker import ProgressTracker
from app.db.repositories.escalation_repo import EscalationLogger
from app.rag.pipeline import RAGPipeline
from app.models.routing import RoutingResult, EscalationInfo, HybridOptions
from app.models.escalation import EscalationDecision
from app.models.session import Session
from app.utils.errors import (
    GeminiTimeoutError, GeminiAPIError, RateLimitError,
    OllamaConnectionError, OllamaTimeoutError, NoProviderAvailableError,
)

logger = logging.getLogger("ai-agent-hybrid.decision")


class DecisionEngine:
    """Orchestrator utama Hybrid Routing."""

    def __init__(
        self,
        chat_service: ChatService,
        generate_service: GenerateService,
        session_mgr: SessionManager,
        escalation_checker: EscalationChecker,
        progress_tracker: ProgressTracker,
        escalation_logger: EscalationLogger,
        rag_pipeline: RAGPipeline | None = None,
    ):
        self.chat = chat_service
        self.generate = generate_service
        self.session_mgr = session_mgr
        self.checker = escalation_checker
        self.tracker = progress_tracker
        self.esc_logger = escalation_logger
        self.rag = rag_pipeline

    async def route(
        self,
        session_id: str | None,
        message: str,
        options: HybridOptions | None = None,
        images: list[str] | None = None,
    ) -> RoutingResult:
        """Main routing logic."""
        options = options or HybridOptions()
        chat_mode = options.chat_mode  # NEW — extract chat_mode
        generator = "gemini" if chat_mode == "gemini" else "ollama"

        # === STEP 0: Force generate ===
        if options.force_generate:
            if not session_id:
                raise ValueError("session_id diperlukan untuk force_generate")
            gen_result = await self.generate.generate_tor(
                session_id, mode="escalation", generator=generator,
            )
            return RoutingResult(
                session_id=session_id,
                action_taken="FORCE_GENERATE",
                generate_response=gen_result,
            )

        # === STEP 1: Get/create session ===
        if session_id:
            session = await self.session_mgr.get(session_id)
        else:
            session = await self.session_mgr.create()
            session_id = session.id

        # Check if already completed
        if session.state == "COMPLETED" and session.generated_tor:
            return RoutingResult(
                session_id=session_id,
                action_taken="CHAT",
                chat_response=ChatResult(
                    session_id=session_id,
                    status="COMPLETED",
                    message="TOR sudah dibuat sebelumnya. Kirim pesan untuk memulai revisi.",
                    extracted_data=session.extracted_data,
                    missing_fields=[],
                    confidence=1.0,
                    completeness_score=session.completeness_score,
                    raw_llm_response="",
                ),
            )

        # Check if generating
        if session.state == "GENERATING":
            return RoutingResult(
                session_id=session_id,
                action_taken="CHAT",
                chat_response=ChatResult(
                    session_id=session_id,
                    status="GENERATING",
                    message="Sedang memproses TOR Anda, mohon tunggu.",
                    extracted_data=session.extracted_data,
                    missing_fields=[],
                    confidence=1.0,
                    completeness_score=session.completeness_score,
                    raw_llm_response="",
                ),
            )

        # === STEP 2: Pre-routing escalation check ===
        # Escalation is disabled. Always continue to chat and generate when user requests.

        # === STEP 3: Get RAG context ===
        rag_context = None
        if self.rag:
            try:
                rag_context = await self.rag.retrieve(message, top_k=3)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        # === STEP 4: Chat with LLM (pass chat_mode + think + images) ===
        chat_result = await self.chat.process_message(
            session_id=session_id,
            message=message,
            rag_context=rag_context,
            chat_mode=chat_mode,
            think=options.think,
            model_preference=options.model_preference,
            images=images,
        )

        # === STEP 5: Update progress ===
        filled_count = len(chat_result.extracted_data.filled_fields())
        self.tracker.update_after_chat(
            session_id, chat_result.completeness_score, filled_count
        )

        # === STEP 6: Post-routing decision ===
        if chat_result.status in ("READY_TO_GENERATE", "ESCALATE_TO_GEMINI"):
            # Escalation is disabled — always use standard generation.
            mode = "standard"

            try:
                gen_result = await self.generate.generate_tor(
                    session_id, mode=mode, generator=generator,
                )
                # Tentukan action_taken berdasarkan generator yang dipakai
                if gen_result.tor_document.metadata.generator == "ollama":
                    action = "GENERATE_LOCAL"
                elif mode == "standard":
                    action = "GENERATE_STANDARD"
                else:
                    action = "GENERATE_ESCALATION"

                return RoutingResult(
                    session_id=session_id,
                    action_taken=action,
                    chat_response=chat_result,
                    generate_response=gen_result,
                )
            except (
                GeminiTimeoutError, RateLimitError, GeminiAPIError,
                OllamaConnectionError, OllamaTimeoutError, NoProviderAvailableError,
            ) as e:
                logger.error(f"Generate failed after READY: {e}")
                await self.session_mgr.update(session_id, state="CHATTING")
                return RoutingResult(
                    session_id=session_id,
                    action_taken="CHAT",
                    chat_response=ChatResult(
                        session_id=session_id,
                        status="NEED_MORE_INFO",
                        message=f"Maaf, sistem generate sedang bermasalah: {str(e)[:100]}. "
                                "Coba lagi nanti atau ganti generator.",
                        extracted_data=chat_result.extracted_data,
                        missing_fields=chat_result.missing_fields,
                        confidence=0.0,
                        completeness_score=chat_result.completeness_score,
                        raw_llm_response="",
                    ),
                )

        # Default: NEED_MORE_INFO or unknown status → continue chatting
        return RoutingResult(
            session_id=session_id,
            action_taken="CHAT",
            chat_response=chat_result,
        )

    async def _handle_escalation(
        self,
        session_id: str,
        session: Session,
        decision: EscalationDecision,
        triggering_message: str,
        options: HybridOptions | None = None,
    ) -> RoutingResult:
        """Handle escalation: log, update state, generate via provider."""
        chat_mode = options.chat_mode if options else "local"
        generator = "gemini" if chat_mode == "gemini" else "ollama"

        # Log escalation
        await self.esc_logger.log(
            session_id, decision, session.turn_count,
            session.completeness_score, triggering_message
        )

        # Update session state
        await self.session_mgr.update(
            session_id,
            state="ESCALATED",
            escalation_reason=decision.reason,
        )

        # Generate via provider (escalation mode)
        try:
            gen_result = await self.generate.generate_tor(
                session_id, mode="escalation", generator=generator,
            )
        except (
            GeminiTimeoutError, RateLimitError, GeminiAPIError,
            OllamaConnectionError, OllamaTimeoutError, NoProviderAvailableError,
        ) as e:
            logger.error(f"Generate failed during escalation: {e}")
            # Rollback state
            await self.session_mgr.update(session_id, state="CHATTING")
            return RoutingResult(
                session_id=session_id,
                action_taken="CHAT",
                chat_response=ChatResult(
                    session_id=session_id,
                    status="NEED_MORE_INFO",
                    message="Maaf, sistem sedang sibuk. Coba lagi nanti. "
                            "Sementara itu, beri saya informasi tambahan "
                            "agar TOR bisa lebih lengkap.",
                    extracted_data=session.extracted_data,
                    missing_fields=session.extracted_data.missing_fields(),
                    confidence=0.0,
                    completeness_score=session.completeness_score,
                    raw_llm_response="",
                ),
            )

        action = (
            "GENERATE_LOCAL"
            if gen_result.tor_document.metadata.generator == "ollama"
            else "GENERATE_ESCALATION"
        )
        return RoutingResult(
            session_id=session_id,
            action_taken=action,
            generate_response=gen_result,
            escalation_info=EscalationInfo(
                triggered_by=decision.rule_name,
                reason=decision.reason,
                turn_count=session.turn_count,
                completeness_at_escalation=session.completeness_score,
            ),
        )
