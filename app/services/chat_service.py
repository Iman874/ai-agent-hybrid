import asyncio
import logging
from dataclasses import dataclass
from typing import AsyncGenerator

from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.core.completeness import calculate_completeness, merge_extracted_data
from app.models.tor import TORData, LLMParsedResponse
from app.models.session import Session, ChatMessage
from app.services.stream_service import StreamEvent
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
    """Orchestrator utama Chat Engine — multi-provider."""

    def __init__(
        self,
        ollama: OllamaProvider,
        session_mgr: SessionManager,
        prompt_builder: PromptBuilder,
        parser: ResponseParser,
        rag_pipeline: RAGPipeline | None = None,
        gemini_chat=None,
    ):
        self.ollama = ollama
        self.gemini_chat = gemini_chat
        self.session_mgr = session_mgr
        self.prompt_builder = prompt_builder
        self.parser = parser
        self.rag_pipeline = rag_pipeline
        self._logger = logger

    def _get_provider(self, chat_mode: str):
        """Return LLM provider berdasarkan chat_mode."""
        if chat_mode == "gemini" and self.gemini_chat:
            return self.gemini_chat
        if chat_mode == "gemini" and not self.gemini_chat:
            self._logger.warning("Gemini chat requested but provider not available. Falling back to Ollama.")
        return self.ollama

    async def process_message(
        self,
        session_id: str | None,
        message: str,
        rag_context: str | None = None,
        chat_mode: str = "local",
        think: bool = True,
        images: list[str] | None = None,
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

        # === Step 3.5: Inject images ke user message terakhir ===
        if images:
            for msg in reversed(messages):
                if msg["role"] == "user":
                    msg["images"] = images
                    break

        # === Step 4 + 5: Call LLM with retry ===
        provider = self._get_provider(chat_mode)
        parsed = await self._call_with_retry(messages, session, max_retries=2, provider=provider, think=think)

        # === Step 6: Merge extracted data ===
        new_data = parsed.data or parsed.extracted_so_far or parsed.partial_data or TORData()
        extracted = merge_extracted_data(session.extracted_data, new_data)
        completeness = calculate_completeness(extracted)

        # === Step 7: Update session ===
        await self.session_mgr.append_message(session.id, "user", message)
        await self.session_mgr.append_message(
            session.id, "assistant", parsed.message, parsed.status
        )

        # === Auto-title: set dari pesan pertama user ===
        if session.turn_count == 0:
            title = message[:40].strip()
            if len(message) > 40:
                title += "..."
            await self.session_mgr.update(session.id, title=title)

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

    async def process_message_stream(
        self,
        session_id: str | None,
        message: str,
        rag_context: str | None = None,
        chat_mode: str = "local",
        think: bool = True,
        images: list[str] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Streaming version dari process_message()."""
        # === Step 1: Session ===
        if session_id is None:
            session = await self.session_mgr.create()
            self._logger.info(f"New session created: {session.id}")
        else:
            session = await self.session_mgr.get(session_id)
            self._logger.info(f"Continuing session: {session.id}, turn={session.turn_count}")

        yield StreamEvent(type="status", response={"session_id": session.id})

        # === Step 2: RAG retrieval ===
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
        history = await self.session_mgr.get_chat_history(session.id)
        messages = self.prompt_builder.build_chat_messages(
            chat_history=history,
            user_message=message,
            rag_context=rag_context,
        )

        # === Step 3.5: Inject images ke user message terakhir ===
        if images:
            for msg in reversed(messages):
                if msg["role"] == "user":
                    msg["images"] = images
                    break

        # === Step 4: Stream dari provider ===
        provider = self._get_provider(chat_mode)
        accumulated_content = ""
        has_thinking = False

        try:
            async for chunk in provider.chat_stream(messages, think=think):
                thinking_text = chunk.get("thinking", "")
                token_text = chunk.get("token", "")
                is_done = chunk.get("done", False)

                if thinking_text:
                    if not has_thinking:
                        yield StreamEvent(type="thinking_start")
                        has_thinking = True
                    yield StreamEvent(type="thinking_token", token=thinking_text)

                if token_text and has_thinking:
                    yield StreamEvent(type="thinking_end")
                    has_thinking = False

                if token_text:
                    yield StreamEvent(type="token", token=token_text)
                    accumulated_content += token_text

                if is_done:
                    break

        except Exception as e:
            self._logger.error(f"Stream error: {e}")
            if has_thinking:
                yield StreamEvent(type="thinking_end")
            yield StreamEvent(type="error", error=str(e))
            return

        if has_thinking:
            # Pastikan indikator thinking ditutup jika provider selesai tanpa token output.
            yield StreamEvent(type="thinking_end")

        # === Step 5 + 6: Parse response + update session ===
        try:
            try:
                data = self.parser.extract_json(accumulated_content)
                parsed = self.parser.validate_parsed(data)
            except LLMParseError:
                parsed = self._build_fallback(session, accumulated_content)

            new_data = parsed.data or parsed.extracted_so_far or parsed.partial_data or TORData()
            extracted = merge_extracted_data(session.extracted_data, new_data)
            completeness = calculate_completeness(extracted)

            await self.session_mgr.append_message(session.id, "user", message)
            await self.session_mgr.append_message(
                session.id,
                "assistant",
                parsed.message,
                parsed.status,
            )

            # Auto-title: set dari pesan pertama user.
            if session.turn_count == 0:
                title = message[:40].strip()
                if len(message) > 40:
                    title += "..."
                await self.session_mgr.update(session.id, title=title)

            next_turn_count = session.turn_count + 1
            await self.session_mgr.update(
                session.id,
                state=self._map_state(parsed.status),
                turn_count=next_turn_count,
                extracted_data=extracted,
                completeness_score=completeness,
            )

            result = ChatResult(
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

            yield StreamEvent(
                type="done",
                response={
                    "session_id": session.id,
                    "message": result.message,
                    "state": {
                        "status": result.status,
                        "turn_count": next_turn_count,
                        "completeness_score": result.completeness_score,
                        "filled_fields": result.extracted_data.filled_fields(),
                        "missing_fields": result.missing_fields,
                    },
                    "extracted_data": result.extracted_data.model_dump() if result.extracted_data else None,
                },
            )

        except Exception as e:
            self._logger.error(f"Stream finalize error: {e}")
            yield StreamEvent(type="error", error=str(e))
            return

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
        provider=None,
        think: bool = True,
    ) -> LLMParsedResponse:
        """
        Call LLM provider dan parse response. Retry jika JSON parse gagal.

        Strategi:
        - Attempt 0: normal call
        - Attempt 1: tambah pesan instruksi JSON
        - Attempt 2: tambah pesan instruksi lagi
        - Jika semua gagal: return fallback response
        """
        provider = provider or self.ollama
        last_error = None
        working_messages = messages.copy()

        for attempt in range(max_retries + 1):
            try:
                raw_response = await provider.chat(working_messages, think=think)
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
