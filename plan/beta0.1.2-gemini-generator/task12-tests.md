# Task 12 — Unit Tests & Integration Test

## 1. Judul Task

Buat unit tests (tanpa Gemini API) dan integration test (dengan Gemini API) untuk seluruh Gemini Generator module.

## 2. Deskripsi

Unit tests menggunakan mock GeminiProvider untuk menguji PostProcessor, TORCache, CostController, dan GeminiPromptBuilder tanpa memerlukan API key. Integration test menggunakan Gemini API asli untuk verify end-to-end flow.

## 3. Tujuan Teknis

- `tests/test_generate_unit.py` — unit tests (tanpa Gemini API key)
- `tests/test_generate_integration.py` — integration test (dengan Gemini API key)
- Coverage: PostProcessor, TORCache, CostController, PromptBuilder, GenerateService (mocked)

## 4. Scope

### Yang dikerjakan
- `tests/test_generate_unit.py` — 10+ unit tests
- `tests/test_generate_integration.py` — 3+ integration tests

### Yang tidak dikerjakan
- Performance benchmarks
- Load testing

## 5. Langkah Implementasi

### Step 1: Buat `tests/test_generate_unit.py`

```python
"""Unit tests Gemini Generator — tidak membutuhkan API key."""
import pytest
from app.core.post_processor import PostProcessor
from app.core.gemini_prompt_builder import GeminiPromptBuilder, format_chat_history
from app.models.tor import TORData
from app.models.session import ChatMessage


class TestPostProcessor:
    def test_clean_code_block_wrapper(self):
        raw = "```markdown\n# TOR\nIni konten.\n```"
        result = PostProcessor.process(raw)
        assert not result.content.startswith("```")

    def test_word_count(self):
        result = PostProcessor.process("satu dua tiga empat lima enam")
        assert result.word_count == 6

    def test_has_assumptions_true(self):
        result = PostProcessor.process("Ini [ASUMSI] konten asumsi.")
        assert result.has_assumptions is True

    def test_has_assumptions_false(self):
        result = PostProcessor.process("Ini konten tanpa asumsi.")
        assert result.has_assumptions is False

    def test_missing_sections_detected(self):
        result = PostProcessor.process("## 1. Latar Belakang\nIni saja.")
        assert "Tujuan" in result.missing_sections

    def test_all_sections_present(self):
        tor = "Latar Belakang\nTujuan\nRuang Lingkup\nOutput\nTimeline"
        result = PostProcessor.process(tor)
        assert result.missing_sections == []


class TestGeminiPromptBuilder:
    def test_standard_with_rag(self):
        data = TORData(judul="Workshop AI")
        prompt = GeminiPromptBuilder.build_standard(data, rag_examples="Contoh TOR")
        assert "Workshop AI" in prompt
        assert "Contoh TOR" in prompt

    def test_standard_without_rag(self):
        data = TORData(judul="Workshop AI")
        prompt = GeminiPromptBuilder.build_standard(data)
        assert "Tidak ada referensi tersedia" in prompt

    def test_escalation_with_history(self):
        history = [
            ChatMessage(session_id="x", role="user", content="Buat TOR"),
        ]
        formatted = format_chat_history(history)
        prompt = GeminiPromptBuilder.build_escalation(formatted)
        assert "[USER]: Buat TOR" in prompt

    def test_escalation_with_partial_data(self):
        data = TORData(judul="Test TOR")
        prompt = GeminiPromptBuilder.build_escalation("chat...", partial_data=data)
        assert "Test TOR" in prompt
        assert "DATA PARSIAL" in prompt
```

### Step 2: Buat `tests/test_generate_integration.py`

```python
"""
Integration tests Gemini Generator.
REQUIRES: Valid GEMINI_API_KEY in .env
"""
import pytest
import pytest_asyncio
import os

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def generate_pipeline(tmp_path):
    """Setup GenerateService with test DB."""
    test_db = str(tmp_path / "test_generate.db")
    from app.db.database import init_db
    await init_db(test_db)

    from app.config import Settings
    from app.core.session_manager import SessionManager
    from app.ai.gemini_provider import GeminiProvider
    from app.core.gemini_prompt_builder import GeminiPromptBuilder
    from app.core.post_processor import PostProcessor
    from app.core.cost_controller import CostController
    from app.db.repositories.cache_repo import TORCache
    from app.services.generate_service import GenerateService

    settings = Settings()
    if not settings.gemini_api_key or settings.gemini_api_key == "your-api-key-here":
        pytest.skip("GEMINI_API_KEY not configured")

    session_mgr = SessionManager(test_db)
    return {
        "service": GenerateService(
            gemini=GeminiProvider(settings),
            session_mgr=session_mgr,
            rag_pipeline=None,
            prompt_builder=GeminiPromptBuilder(),
            post_processor=PostProcessor(),
            cache=TORCache(test_db),
            cost_ctrl=CostController(session_mgr, settings),
        ),
        "session_mgr": session_mgr,
    }


async def test_generate_standard(generate_pipeline):
    session_mgr = generate_pipeline["session_mgr"]
    service = generate_pipeline["service"]

    # Create session with data
    from app.models.tor import TORData
    session = await session_mgr.create()
    data = TORData(
        judul="Workshop AI untuk ASN",
        tujuan="Meningkatkan kompetensi digital ASN",
        ruang_lingkup="30 peserta, 3 hari pelatihan",
    )
    await session_mgr.update(
        session.id, extracted_data=data,
        completeness_score=0.5, state="READY"
    )

    result = await service.generate_tor(session.id, mode="standard")
    assert result.cached is False
    assert result.tor_document.metadata.word_count > 0
    assert "TOR" in result.tor_document.content or "Workshop" in result.tor_document.content


async def test_generate_cached(generate_pipeline):
    session_mgr = generate_pipeline["session_mgr"]
    service = generate_pipeline["service"]

    from app.models.tor import TORData
    session = await session_mgr.create()
    data = TORData(judul="Test Cache TOR", tujuan="Testing cache")
    await session_mgr.update(
        session.id, extracted_data=data,
        completeness_score=0.5, state="READY"
    )

    # First call
    result1 = await service.generate_tor(session.id)
    assert result1.cached is False

    # Second call should be cached
    result2 = await service.generate_tor(session.id)
    assert result2.cached is True
```

### Step 3: Jalankan tests

```bash
# Unit tests (tanpa API key)
.\venv\Scripts\pytest.exe tests/test_generate_unit.py -v

# Integration test (butuh API key)
.\venv\Scripts\pytest.exe tests/test_generate_integration.py -v
```

## 6. Output yang Diharapkan

```
tests/test_generate_unit.py::TestPostProcessor::test_clean_code_block_wrapper PASSED
tests/test_generate_unit.py::TestPostProcessor::test_word_count PASSED
...
tests/test_generate_unit.py::TestGeminiPromptBuilder::test_standard_with_rag PASSED
...
====================== 10 passed in X.XXs ======================
```

## 7. Dependencies

- **Semua task 01-11** harus selesai
- External (integration): Valid `GEMINI_API_KEY`

## 8. Acceptance Criteria

- [ ] `pytest tests/test_generate_unit.py -v` → 10+ tests PASSED tanpa API key
- [ ] `pytest tests/test_generate_integration.py -v` → PASSED dengan API key (atau SKIP jika tidak ada key)
- [ ] PostProcessor tests cover: clean formatting, word count, assumptions, section check
- [ ] PromptBuilder tests cover: standard ± RAG, escalation ± partial data

## 9. Estimasi

**Medium** — ~2 jam
