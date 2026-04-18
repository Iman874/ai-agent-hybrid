# Task 07 — DecisionEngine Core: Routing Logic Utama

## 1. Judul Task

Implementasikan `DecisionEngine` — orchestrator utama yang menggabungkan EscalationChecker, ProgressTracker, ChatService, dan GenerateService menjadi satu pipeline routing hybrid.

## 2. Deskripsi

DecisionEngine adalah class sentral yang dipanggil oleh HybridController (beta0.1.4). Ia menerima `session_id` + `message` + `options`, lalu menentukan apakah pesan dikirim ke local LLM (chat) atau langsung eskalasi ke Gemini (generate). Ini adalah "otak" dari seluruh sistem.

## 3. Tujuan Teknis

- `route(session_id, message, options) → RoutingResult` — entry point utama
- Step 0: Force generate bypass
- Step 1: Session state check (COMPLETED, GENERATING)
- Step 2: Pre-routing escalation check
- Step 3: RAG context retrieval (optional)
- Step 4: Chat with local LLM
- Step 5: Update progress tracker
- Step 6: Post-routing decision (CHAT / GENERATE_STANDARD / GENERATE_ESCALATION)
- `_handle_escalation()` — private method untuk handle eskalasi

## 4. Scope

### Yang dikerjakan
- `app/core/decision_engine.py` — class `DecisionEngine`

### Yang tidak dikerjakan
- HTTP endpoint (itu beta0.1.4)
- Wiring di main.py (itu task terpisah)

## 5. Langkah Implementasi

### Step 1: Buat `app/core/decision_engine.py`

```python
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
from app.utils.errors import GeminiTimeoutError, GeminiAPIError, RateLimitError

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
    ) -> RoutingResult:
        """Main routing logic."""
        options = options or HybridOptions()

        # === STEP 0: Force generate ===
        if options.force_generate:
            if not session_id:
                raise ValueError("session_id diperlukan untuk force_generate")
            gen_result = await self.generate.generate_tor(
                session_id, mode="escalation"
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
        progress = self.tracker.get(session_id)
        escalation = self.checker.check_pre_routing(message, session, progress)

        if escalation.should_escalate:
            return await self._handle_escalation(
                session_id, session, escalation, message
            )

        # === STEP 3: Get RAG context ===
        rag_context = None
        if self.rag:
            try:
                rag_context = await self.rag.retrieve(message, top_k=3)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        # === STEP 4: Chat with local LLM ===
        chat_result = await self.chat.process_message(
            session_id=session_id,
            message=message,
            rag_context=rag_context,
        )

        # === STEP 5: Update progress ===
        filled_count = len(chat_result.extracted_data.filled_fields())
        self.tracker.update_after_chat(
            session_id, chat_result.completeness_score, filled_count
        )

        # === STEP 6: Post-routing decision ===
        if chat_result.status == "READY_TO_GENERATE":
            # Edge case: LLM says READY but score is low → use escalation mode
            if chat_result.completeness_score < 0.5:
                logger.warning(
                    f"LLM says READY but score only {chat_result.completeness_score:.2f}. "
                    "Overriding to escalation mode."
                )
                mode = "escalation"
            else:
                mode = "standard"

            try:
                gen_result = await self.generate.generate_tor(
                    session_id, mode=mode
                )
                return RoutingResult(
                    session_id=session_id,
                    action_taken="GENERATE_STANDARD" if mode == "standard" else "GENERATE_ESCALATION",
                    chat_response=chat_result,
                    generate_response=gen_result,
                )
            except (GeminiTimeoutError, RateLimitError, GeminiAPIError) as e:
                logger.error(f"Generate failed after READY: {e}")
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
                        extracted_data=chat_result.extracted_data,
                        missing_fields=chat_result.missing_fields,
                        confidence=0.0,
                        completeness_score=chat_result.completeness_score,
                        raw_llm_response="",
                    ),
                )

        elif chat_result.status == "ESCALATE_TO_GEMINI":
            try:
                gen_result = await self.generate.generate_tor(
                    session_id, mode="escalation"
                )
                return RoutingResult(
                    session_id=session_id,
                    action_taken="GENERATE_ESCALATION",
                    chat_response=chat_result,
                    generate_response=gen_result,
                    escalation_info=EscalationInfo(
                        triggered_by="llm_decision",
                        reason=chat_result.escalation_reason or "LLM memutuskan eskalasi",
                        turn_count=session.turn_count + 1,
                        completeness_at_escalation=chat_result.completeness_score,
                    ),
                )
            except (GeminiTimeoutError, RateLimitError, GeminiAPIError) as e:
                logger.error(f"Generate failed after LLM escalation: {e}")
                await self.session_mgr.update(session_id, state="CHATTING")
                return RoutingResult(
                    session_id=session_id,
                    action_taken="CHAT",
                    chat_response=ChatResult(
                        session_id=session_id,
                        status="NEED_MORE_INFO",
                        message="Maaf, sistem sedang sibuk. Coba lagi nanti.",
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
    ) -> RoutingResult:
        """Handle escalation: log, update state, generate via Gemini."""
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

        # Generate via Gemini (escalation mode)
        try:
            gen_result = await self.generate.generate_tor(
                session_id, mode="escalation"
            )
        except (GeminiTimeoutError, RateLimitError, GeminiAPIError) as e:
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

        return RoutingResult(
            session_id=session_id,
            action_taken="GENERATE_ESCALATION",
            generate_response=gen_result,
            escalation_info=EscalationInfo(
                triggered_by=decision.rule_name,
                reason=decision.reason,
                turn_count=session.turn_count,
                completeness_at_escalation=session.completeness_score,
            ),
        )
```

### Step 2: Verifikasi

Karena DecisionEngine butuh ChatService (Ollama) dan GenerateService (Gemini), verifikasi lengkap dilakukan di Task 10 (Integration Test). Verifikasi struktur bisa dilakukan dengan import check:

```python
from app.core.decision_engine import DecisionEngine
print("DecisionEngine imported successfully")
print("ALL DECISION ENGINE IMPORT TESTS PASSED")
```

## 6. Output yang Diharapkan

`RoutingResult` yang berisi action (CHAT/GENERATE_STANDARD/GENERATE_ESCALATION/FORCE_GENERATE) beserta response dan escalation info.

## 7. Dependencies

- **Task 01** — `RoutingResult`, `EscalationInfo`, `HybridOptions`
- **Task 03** — `EscalationChecker`
- **Task 04** — `ProgressTracker`
- **Task 06** — `EscalationLogger`
- **beta0.1.0** — `ChatService`, `SessionManager`
- **beta0.1.2** — `GenerateService`
- **beta0.1.1** — `RAGPipeline` (optional)

## 8. Acceptance Criteria

- [ ] `route()` menjalankan semua 6 steps sesuai flow
- [ ] Force generate bypass semua logic
- [ ] COMPLETED session return pesan info
- [ ] GENERATING session return pesan tunggu
- [ ] Pre-routing escalation triggers → generate escalation mode
- [ ] READY_TO_GENERATE dari LLM → generate standard (atau escalation jika score < 0.5)
- [ ] ESCALATE_TO_GEMINI dari LLM → generate escalation
- [ ] Gemini failure → rollback state ke CHATTING, return fallback chat
- [ ] Progress tracker di-update setelah chat

## 9. Estimasi

**High** — ~3 jam
