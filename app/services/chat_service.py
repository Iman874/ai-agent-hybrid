import asyncio
import logging
from dataclasses import dataclass

from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.core.completeness import calculate_completeness, merge_extracted_data
from app.models.tor import TORData, LLMParsedResponse
from app.models.session import Session, ChatMessage
from app.utils.errors import LLMParseError
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger("ai-agent-hybrid.chat")


@dataclass
class ChatResult:
    """Hasil dari satu turn chat."""
    session_id: str
    status: str                          # NEED_MORE_INFO | READY_TO_GENERATE | ESCALATE_TO_GEMINI
    message: str                         # pesan natural untuk user
    extracted_data: TORData              # data TOR terkumpul
    missing_fields: list[str]            # field yang masih kosong
    confidence: float                    # 0.0 - 1.0
    completeness_score: float            # 0.0 - 1.0
    raw_llm_response: str               # raw JSON dari LLM
    escalation_reason: str | None = None # alasan jika ESCALATE


class ChatService:
    """Orchestrator utama Chat Engine."""

    def __init__(
        self,
        ollama: OllamaProvider,
        session_mgr: SessionManager,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        rag_pipeline: RAGPipeline | None = None,
    ):
        self.ollama = ollama
        self.session_mgr = session_mgr
        self.prompt_builder = prompt_builder
        self.parser = parser
        self.rag_pipeline = rag_pipeline
        self._logger = logger

    async def process_message(
        self,
        session_id: str | None,
        message: str,
        rag_context: str | None = None,
    ) -> ChatResult:
        """
        Process satu turn chat. Entry point utama.
        """
        # === Step 1: Session ===
        if session_id is None:
            session = await self.session_mgr.create()
            self._logger.info(f"New session created: {session.id}")
        else:
            session = await self.session_mgr.get(session_id)
            self._logger.info(f"Continuing session: {session.id}, turn={session.turn_count}")

        # === Step 2: Chat history ===
        history = await self.session_mgr.get_chat_history(session.id)

        # === RAG RETRIEVAL ===
        if rag_context is None and self.rag_pipeline is not None:
            try:
                rag_context = await self.rag_pipeline.retrieve(query=message)
                if rag_context:
                    self._logger.debug(
                        f"RAG context retrieved: {len(rag_context)} chars"
                    )
            except Exception as e:
                self._logger.warning(f"RAG retrieval failed, continuing without: {e}")
                rag_context = None

        # === Step 3: Build prompt ===
        messages = self.prompt_builder.build_chat_messages(
            chat_history=history,
            user_message=message,
            rag_context=rag_context,
        )

        # === Step 4 + 5: Call Ollama with retry ===
        parsed = await self._call_with_retry(messages, session, max_retries=2)

        # === Step 6: Merge extracted data ===
        new_data = parsed.data or parsed.extracted_so_far or parsed.partial_data or TORData()
        extracted = merge_extracted_data(session.extracted_data, new_data)
        completeness = calculate_completeness(extracted)

        # === Step 7: Update session ===
        await self.session_mgr.append_message(session.id, "user", message)
        await self.session_mgr.append_message(
            session.id, "assistant", parsed.message, parsed.status
        )
        await self.session_mgr.update(
            session.id,
            state=self._map_state(parsed.status),
            turn_count=session.turn_count + 1,
            extracted_data=extracted,
            completeness_score=completeness,
        )

        # === Step 8: Return result ===
        self._logger.info(
            f"Turn {session.turn_count + 1} complete: "
            f"status={parsed.status}, completeness={completeness}"
        )
        return ChatResult(
            session_id=session.id,
            status=parsed.status,
            message=parsed.message,
            extracted_data=extracted,
            missing_fields=extracted.missing_fields(),
            confidence=parsed.confidence,
            completeness_score=completeness,
            raw_llm_response=parsed.model_dump_json(),
            escalation_reason=parsed.reason,
        )

    async def get_session(self, session_id: str) -> Session:
        """Ambil session (delegasi ke SessionManager)."""
        return await self.session_mgr.get(session_id)

    async def get_chat_history(self, session_id: str) -> list[ChatMessage]:
        """Ambil chat history (delegasi ke SessionManager)."""
        return await self.session_mgr.get_chat_history(session_id)

    async def get_extracted_data(self, session_id: str) -> TORData:
        """Ambil extracted data dari session."""
        session = await self.session_mgr.get(session_id)
        return session.extracted_data

    # ─── Private Methods ────────────────────────────────────────────

    async def _call_with_retry(
        self,
        messages: list[dict],
        session: Session,
        max_retries: int = 2,
    ) -> LLMParsedResponse:
        """
        Call Ollama dan parse response. Retry jika JSON parse gagal.

        Strategi:
        - Attempt 0: normal call
        - Attempt 1: tambah pesan instruksi JSON
        - Attempt 2: tambah pesan instruksi lagi
        - Jika semua gagal: return fallback response
        """
        last_error = None
        working_messages = messages.copy()

        for attempt in range(max_retries + 1):
            try:
                raw_response = await self.ollama.chat(working_messages)
                data = self.parser.extract_json(raw_response["content"])
                validated = self.parser.validate_parsed(data)
                self._logger.debug(f"Parse successful on attempt {attempt + 1}")
                return validated

            except LLMParseError as e:
                last_error = e
                self._logger.warning(
                    f"Parse failed on attempt {attempt + 1}/{max_retries + 1}: {e.details}"
                )

                if attempt < max_retries:
                    # Tambah instruksi agar LLM output JSON
                    working_messages.append({
                        "role": "user",
                        "content": (
                            "PENTING: Jawab HANYA dalam format JSON yang diminta. "
                            "Tanpa teks tambahan di luar JSON."
                        ),
                    })
                    await asyncio.sleep(1)  # backoff sederhana

        # Semua retry gagal → fallback
        self._logger.error(f"All {max_retries + 1} parse attempts failed. Using fallback.")
        return self._build_fallback(session, raw_response.get("content", ""))

    def _build_fallback(self, session: Session, raw_content: str) -> LLMParsedResponse:
        """
        Build fallback response jika LLM gagal output JSON setelah semua retry.
        Pertahankan data existing, tampilkan raw text sebagai message.
        """
        return LLMParsedResponse(
            status="NEED_MORE_INFO",
            message=raw_content[:500] if raw_content else "Maaf, saya mengalami kesulitan. Bisa ulangi permintaan Anda?",
            extracted_so_far=session.extracted_data,
            missing_fields=session.extracted_data.missing_fields(),
            confidence=0.0,
        )

    def _map_state(self, status: str) -> str:
        """Map LLM status → session state."""
        return {
            "NEED_MORE_INFO": "CHATTING",
            "READY_TO_GENERATE": "READY",
            "ESCALATE_TO_GEMINI": "ESCALATED",
        }.get(status, "CHATTING")
