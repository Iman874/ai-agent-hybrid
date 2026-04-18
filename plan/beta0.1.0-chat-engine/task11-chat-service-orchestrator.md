# Task 11 — ChatService Orchestrator

## 1. Judul Task

Implementasi `ChatService` — orchestrator utama yang menghubungkan semua komponen Chat Engine.

## 2. Deskripsi

Membuat class `ChatService` yang menjadi **entry point** logic Chat Engine. Class ini mengorkestrasi seluruh flow: session management → prompt building → Ollama call → response parsing → data merging → session update → return result. Termasuk retry logic jika LLM gagal output JSON.

## 3. Tujuan Teknis

- `ChatService.process_message()` adalah satu-satunya method yang dipanggil dari luar
- Method ini menjalankan seluruh 7 step flow yang didefinisikan di modul
- Retry logic: jika parse gagal, retry 2x dengan prompt tambahan
- Fallback: jika tetap gagal after retry, return NEED_MORE_INFO dengan raw text
- Data merge: field baru ditambahkan tanpa menghapus field yang sudah ada

## 4. Scope

### Yang dikerjakan
- `app/services/chat_service.py` — class `ChatService`
- Method `process_message()` — orchestrator utama
- Method `_call_with_retry()` — retry logic
- Method `_merge_extracted()` — data merging
- Method `_map_state()` — status → state mapping
- Method `_build_fallback()` — fallback jika parsing gagal total

### Yang tidak dikerjakan
- REST endpoint (itu task 12)
- Decision engine routing (itu beta0.1.3)

## 5. Langkah Implementasi

### Step 1: Buat `app/services/chat_service.py`

```python
import asyncio
import logging
from dataclasses import dataclass

from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.core.completeness import calculate_completeness, merge_extracted_data
from app.models.tor import TORData, LLMParsedResponse, REQUIRED_FIELDS, OPTIONAL_FIELDS
from app.models.session import Session, ChatMessage
from app.utils.errors import LLMParseError

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
    ):
        self.ollama = ollama
        self.session_mgr = session_mgr
        self.prompt_builder = prompt_builder
        self.parser = parser

    async def process_message(
        self,
        session_id: str | None,
        message: str,
        rag_context: str | None = None,
    ) -> ChatResult:
        """
        Process satu turn chat. Entry point utama.

        Flow:
        1. Get/create session
        2. Get chat history
        3. Build prompt
        4. Call Ollama (with retry)
        5. Parse response
        6. Merge extracted data
        7. Update session
        8. Return result
        """
        # === Step 1: Session ===
        if session_id is None:
            session = await self.session_mgr.create()
            logger.info(f"New session created: {session.id}")
        else:
            session = await self.session_mgr.get(session_id)
            logger.info(f"Continuing session: {session.id}, turn={session.turn_count}")

        # === Step 2: Chat history ===
        history = await self.session_mgr.get_chat_history(session.id)

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
        logger.info(
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
                logger.debug(f"Parse successful on attempt {attempt + 1}")
                return validated

            except LLMParseError as e:
                last_error = e
                logger.warning(
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
        logger.error(f"All {max_retries + 1} parse attempts failed. Using fallback.")
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
```

### Step 2: Update `app/services/__init__.py`

```python
from app.services.chat_service import ChatService, ChatResult
```

### Step 3: Test manual (membutuhkan Ollama running)

```python
import asyncio
from app.config import Settings
from app.db.database import init_db
from app.ai.ollama_provider import OllamaProvider
from app.core.session_manager import SessionManager
from app.core.prompt_builder import PromptBuilder
from app.core.response_parser import ResponseParser
from app.services.chat_service import ChatService

async def test():
    settings = Settings()
    await init_db(settings.session_db_path)

    service = ChatService(
        ollama=OllamaProvider(settings),
        session_mgr=SessionManager(settings.session_db_path),
        prompt_builder=PromptBuilder(),
        parser=ResponseParser(),
    )

    # Turn 1: session baru
    result = await service.process_message(
        session_id=None,
        message="Saya ingin buat TOR untuk workshop penerapan AI",
    )
    print(f"Session: {result.session_id}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Completeness: {result.completeness_score}")
    print(f"Filled: {result.extracted_data.filled_fields()}")

    # Turn 2: lanjut session
    result2 = await service.process_message(
        session_id=result.session_id,
        message="Workshopnya 3 hari untuk 30 peserta ASN",
    )
    print(f"\nTurn 2 Status: {result2.status}")
    print(f"Completeness: {result2.completeness_score}")
    print(f"Missing: {result2.missing_fields}")

asyncio.run(test())
```

## 6. Output yang Diharapkan

```
Session: 550e8400-...
Status: NEED_MORE_INFO
Message: Baik, workshop AI terdengar menarik! Bisa ceritakan...
Completeness: 0.17
Filled: ['judul']

Turn 2 Status: NEED_MORE_INFO
Completeness: 0.33
Missing: ['latar_belakang', 'tujuan', 'output', 'timeline']
```

## 7. Dependencies

- **Task 05** — SessionManager
- **Task 07** — OllamaProvider
- **Task 08** — PromptBuilder
- **Task 09** — ResponseParser
- **Task 10** — calculate_completeness, merge_extracted_data

## 8. Acceptance Criteria

- [ ] `process_message(session_id=None, message="...")` buat session baru dan return ChatResult
- [ ] `process_message(session_id="valid", message="...")` lanjutkan session yang ada
- [ ] `process_message(session_id="invalid", ...)` raise `SessionNotFoundError`
- [ ] ChatResult berisi semua field: session_id, status, message, extracted_data, dll
- [ ] Data dari turn sebelumnya tidak hilang (merge benar)
- [ ] Completeness score terupdate setelah setiap turn
- [ ] User message dan assistant response tersimpan di chat_messages
- [ ] Session state terupdate (NEW → CHATTING, CHATTING → READY, dll)
- [ ] Fallback: jika LLM gagal parse 3x, return NEED_MORE_INFO dengan raw text
- [ ] Retry: saat parse gagal, tambahkan instruksi JSON dan retry

## 9. Estimasi

**High** — ~3 jam
