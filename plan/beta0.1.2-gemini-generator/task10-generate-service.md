# Task 10 — GenerateService: Orchestrator Utama

## 1. Judul Task

Implementasikan `GenerateService` — orchestrator yang menggabungkan CostController, Cache, PromptBuilder, GeminiProvider, PostProcessor, dan SessionManager menjadi satu pipeline generate TOR.

## 2. Deskripsi

Service utama yang mengeksekusi seluruh flow: cost check → cache check → get session → get RAG → build prompt → call Gemini (with retry) → post-process → cache → update session → return result.

## 3. Tujuan Teknis

- `generate_tor(session_id, mode, data_override, force_regenerate) → GenerateResult`
- Retry mechanism: max 3 attempts, exponential backoff [2, 5, 10] seconds
- Standard mode: cache check sebelum call Gemini
- Escalation mode: always call Gemini (no cache check)
- Update session state ke `COMPLETED` setelah berhasil
- Validasi completeness_score >= 0.3 untuk standard mode

## 4. Scope

### Yang dikerjakan
- `app/services/generate_service.py` — class `GenerateService`

### Yang tidak dikerjakan
- API endpoint (itu task 11)
- main.py wiring (itu task 11)

## 5. Langkah Implementasi

### Step 1: Buat `app/services/generate_service.py`

```python
import logging
import asyncio

from app.ai.gemini_provider import GeminiProvider
from app.core.session_manager import SessionManager
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history
from app.core.post_processor import PostProcessor
from app.core.cost_controller import CostController
from app.db.repositories.cache_repo import TORCache
from app.rag.pipeline import RAGPipeline
from app.models.generate import (
    TORDocument, TORMetadata, GenerateResult, GeminiResponse
)
from app.models.tor import TORData
from app.utils.errors import (
    GeminiTimeoutError, GeminiAPIError, InsufficientDataError
)

logger = logging.getLogger("ai-agent-hybrid.generate")


class GenerateService:
    """Orchestrator utama untuk TOR generation via Gemini."""

    def __init__(
        self,
        gemini: GeminiProvider,
        session_mgr: SessionManager,
        rag_pipeline: RAGPipeline | None,
        prompt_builder: GeminiPromptBuilder,
        post_processor: PostProcessor,
        cache: TORCache,
        cost_ctrl: CostController,
    ):
        self.gemini = gemini
        self.session_mgr = session_mgr
        self.rag = rag_pipeline
        self.prompt_builder = prompt_builder
        self.post_processor = post_processor
        self.cache = cache
        self.cost_ctrl = cost_ctrl

    async def generate_tor(
        self,
        session_id: str,
        mode: str = "standard",
        data_override: TORData | None = None,
        force_regenerate: bool = False,
    ) -> GenerateResult:
        """Full generate pipeline."""
        logger.info(f"Generate TOR: session={session_id}, mode={mode}")

        # Step 1: Cost check
        await self.cost_ctrl.check(session_id)

        # Step 2: Check cache (standard mode only)
        if not force_regenerate and mode == "standard":
            cached = await self.cache.get(session_id)
            if cached:
                logger.info(f"Serving TOR from cache: session={session_id}")
                return GenerateResult(
                    session_id=session_id, tor_document=cached, cached=True
                )

        # Step 3: Get session data
        session = await self.session_mgr.get(session_id)
        data = data_override or session.extracted_data

        # Validate completeness for standard mode
        if mode == "standard" and session.completeness_score < 0.3:
            raise InsufficientDataError(
                completeness=session.completeness_score,
                missing_fields=data.missing_fields(),
            )

        history = await self.session_mgr.get_chat_history(session_id)

        # Step 4: Get RAG examples (optional)
        rag_examples = None
        if self.rag and data.judul:
            try:
                rag_examples = await self.rag.retrieve(data.judul, top_k=2)
            except Exception as e:
                logger.warning(f"RAG retrieval failed, continuing without: {e}")

        # Step 5: Build prompt
        if mode == "standard":
            prompt = self.prompt_builder.build_standard(data, rag_examples)
        else:
            formatted_history = format_chat_history(history)
            prompt = self.prompt_builder.build_escalation(
                formatted_history, data, rag_examples
            )

        # Step 6: Call Gemini (with retry)
        gemini_response = await self._call_with_retry(
            prompt, session_id, mode, retries=3, backoff=[2, 5, 10]
        )

        # Step 7: Post-process
        processed = self.post_processor.process(gemini_response.text)

        tor_doc = TORDocument(
            content=processed.content,
            metadata=TORMetadata(
                generated_by=self.gemini.model_name,
                mode=mode,
                word_count=processed.word_count,
                generation_time_ms=gemini_response.duration_ms,
                has_assumptions=processed.has_assumptions,
                prompt_tokens=gemini_response.prompt_tokens,
                completion_tokens=gemini_response.completion_tokens,
            )
        )

        # Step 8: Cache & update session
        await self.cache.store(session_id, tor_doc)
        await self.cost_ctrl.log_call(
            session_id, self.gemini.model_name, mode,
            gemini_response.prompt_tokens, gemini_response.completion_tokens,
            gemini_response.duration_ms, success=True
        )
        await self.session_mgr.update(
            session_id,
            state="COMPLETED",
            generated_tor=processed.content,
            gemini_calls_count=session.gemini_calls_count + 1,
            total_tokens_gemini=session.total_tokens_gemini
                + gemini_response.prompt_tokens
                + gemini_response.completion_tokens,
        )

        logger.info(
            f"TOR generated: session={session_id}, mode={mode}, "
            f"words={processed.word_count}, time={gemini_response.duration_ms}ms"
        )
        return GenerateResult(
            session_id=session_id, tor_document=tor_doc, cached=False
        )

    async def _call_with_retry(
        self, prompt: str, session_id: str, mode: str,
        retries: int = 3, backoff: list[int] = [2, 5, 10]
    ) -> GeminiResponse:
        """Call Gemini with retry and backoff."""
        last_error = None
        for attempt in range(retries):
            try:
                return await self.gemini.generate(prompt)
            except (GeminiTimeoutError, GeminiAPIError, Exception) as e:
                last_error = e
                logger.warning(
                    f"Gemini attempt {attempt + 1}/{retries} failed: {e}"
                )
                # Log failed attempt
                await self.cost_ctrl.log_call(
                    session_id, self.gemini.model_name, mode,
                    0, 0, 0, success=False, error_msg=str(e)[:200]
                )
                if attempt < retries - 1:
                    await asyncio.sleep(backoff[attempt])

        raise last_error
```

### Step 2: Verifikasi bersifat integrasi (akan diverifikasi di Task 12)

Karena GenerateService butuh GeminiProvider (butuh API key), verifikasi lengkap dilakukan di Task 12 (Integration Test). Verifikasi unit bisa dilakukan dengan mock di test.

## 6. Output yang Diharapkan

`GenerateResult` berisi `TORDocument` dengan konten TOR markdown, metadata (word count, tokens, duration), dan flag `cached`.

## 7. Dependencies

- **Task 01** — data models
- **Task 04** — GeminiProvider
- **Task 06** — GeminiPromptBuilder
- **Task 07** — PostProcessor
- **Task 08** — TORCache
- **Task 09** — CostController
- **beta0.1.0** — SessionManager
- **beta0.1.1** — RAGPipeline (optional)

## 8. Acceptance Criteria

- [ ] `generate_tor()` berhasil memanggil Gemini dan return `GenerateResult`
- [ ] Cost check di-enforce sebelum call
- [ ] Cache check untuk standard mode (skip Gemini jika ada cache)
- [ ] Completeness check: reject standard mode jika < 30%
- [ ] Retry mechanism: 3 attempts dengan backoff [2, 5, 10] seconds
- [ ] Session state ter-update ke `COMPLETED`
- [ ] TOR ter-cache setelah generate

## 9. Estimasi

**High** — ~3 jam
