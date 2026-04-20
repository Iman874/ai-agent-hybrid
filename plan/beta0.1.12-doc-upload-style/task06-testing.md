# Task 06: Unit & Integration Testing

> **Status**: [x] Selesai
> **Estimasi**: Medium (1–2 jam)
> **Dependency**: Task 01, Task 02
> **Catatan**: UI testing dilakukan manual oleh user. Task ini hanya backend test.

## 1. Deskripsi

Menulis test suite yang memvalidasi:
1. **Integration test**: `POST /generate/from-document` menggunakan active style
2. **Integration test**: `POST /generate/from-document` menerima `style_id` spesifik
3. **Integration test**: `style_id` invalid → return 404
4. **Unit test**: `PostProcessor.process()` menerima style dari generate_doc flow

## 2. Tujuan Teknis

- Memastikan fix bug kritis (task01) berfungsi benar
- Memastikan parameter `style_id` (task02) berjalan
- Tidak ada regresi pada test suite yang sudah ada

## 3. Scope

**Yang dikerjakan:**
- `tests/test_doc_style_integration.py` — integration test endpoint + unit test

**Yang tidak dikerjakan:**
- UI testing (dilakukan manual oleh user)
- Test untuk auto-detect flow extracting (mock Gemini terlalu kompleks untuk scope ini)

## 4. Langkah Implementasi

### 4.1 Buat Test File

- [x] Buat file `tests/test_doc_style_integration.py`:

```python
"""
Tests untuk Beta 0.1.12: Document Upload + Style Integration.
Integration test endpoint dan unit test PostProcessor.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.tor_style import TORStyle, TORSection, TORStyleConfig

pytestmark = pytest.mark.asyncio


# --- Fixtures ---

def _make_test_style(style_id: str = "test_style", name: str = "Test Style") -> TORStyle:
    """Helper: buat TORStyle object untuk testing."""
    return TORStyle(
        id=style_id,
        name=name,
        description="Test style for integration testing",
        is_default=False,
        is_active=True,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00",
        source="manual",
        sections=[
            TORSection(
                id="latar_belakang",
                title="Latar Belakang",
                required=True,
                description="Konteks kegiatan",
            ),
            TORSection(
                id="tujuan",
                title="Tujuan",
                required=True,
                description="Tujuan kegiatan",
            ),
        ],
        config=TORStyleConfig(),
    )


@pytest_asyncio.fixture
async def mock_app():
    """Setup app dengan mock dependencies."""
    test_style = _make_test_style()
    custom_style = _make_test_style("custom_abc", "Custom ABC")

    # Mock StyleManager
    mock_style_mgr = MagicMock()
    mock_style_mgr.get_active_style.return_value = test_style
    mock_style_mgr.get_style.side_effect = lambda sid: (
        custom_style if sid == "custom_abc"
        else (_ for _ in ()).throw(Exception(f"Style {sid} not found"))
    )

    # Mock GeminiProvider
    mock_gemini = AsyncMock()
    mock_gemini.model_name = "gemini-2.5-pro"
    mock_response = MagicMock()
    mock_response.text = "## 1. Latar Belakang\n\nIni latar belakang test.\n\n## 2. Tujuan\n\nIni tujuan test."
    mock_response.duration_ms = 1000
    mock_response.prompt_tokens = 100
    mock_response.completion_tokens = 200
    mock_gemini.generate.return_value = mock_response

    # Mock PostProcessor
    mock_pp = MagicMock()
    mock_processed = MagicMock()
    mock_processed.content = "## TOR Test\n\nKonten test."
    mock_processed.word_count = 50
    mock_processed.has_assumptions = False
    mock_pp.process.return_value = mock_processed

    # Mock TORCache
    mock_cache = AsyncMock()

    # Assign ke app.state
    app.state.gemini_provider = mock_gemini
    app.state.post_processor = mock_pp
    app.state.style_manager = mock_style_mgr
    app.state.rag_pipeline = None
    app.state.tor_cache = mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, mock_style_mgr, mock_pp


# --- Test: Active Style Digunakan ---

class TestActiveStyleUsed:
    async def test_uses_active_style_by_default(self, mock_app):
        """Endpoint harus menggunakan active style jika style_id tidak diberikan."""
        client, style_mgr, post_proc = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", b"Ini dokumen test untuk TOR.", "text/plain")},
            data={"context": "Test context"},
        )

        assert resp.status_code == 200
        # Pastikan get_active_style() dipanggil
        style_mgr.get_active_style.assert_called_once()
        # Pastikan get_style() TIDAK dipanggil (karena tidak ada style_id)
        style_mgr.get_style.assert_not_called()

    async def test_post_processor_receives_style(self, mock_app):
        """PostProcessor.process() harus menerima style parameter."""
        client, style_mgr, post_proc = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", b"Ini dokumen test.", "text/plain")},
            data={"context": ""},
        )

        assert resp.status_code == 200
        # Pastikan process() dipanggil dengan style keyword argument
        post_proc.process.assert_called_once()
        call_kwargs = post_proc.process.call_args
        assert "style" in call_kwargs.kwargs or len(call_kwargs.args) > 1


# --- Test: style_id Parameter ---

class TestStyleIdParameter:
    async def test_specific_style_id(self, mock_app):
        """Endpoint harus menggunakan style spesifik jika style_id diberikan."""
        client, style_mgr, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", b"Dokumen test.", "text/plain")},
            data={"context": "", "style_id": "custom_abc"},
        )

        assert resp.status_code == 200
        # get_style() harus dipanggil dengan style_id
        style_mgr.get_style.assert_called_once_with("custom_abc")
        # get_active_style() TIDAK boleh dipanggil
        style_mgr.get_active_style.assert_not_called()

    async def test_invalid_style_id_returns_404(self, mock_app):
        """style_id yang tidak ada harus return 404."""
        client, _, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", b"Dokumen test.", "text/plain")},
            data={"context": "", "style_id": "tidak_ada"},
        )

        assert resp.status_code == 404

    async def test_no_style_id_backward_compatible(self, mock_app):
        """Tanpa style_id harus tetap berfungsi (backward compatible)."""
        client, style_mgr, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", b"Test.", "text/plain")},
            data={"context": ""},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "tor_document" in data
        assert "session_id" in data


# --- Test: Response Format ---

class TestResponseFormat:
    async def test_response_contains_tor_document(self, mock_app):
        """Response harus mengandung tor_document dan session_id."""
        client, _, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", b"Dokumen sumber.", "text/plain")},
            data={"context": "Buat TOR workshop."},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"].startswith("doc-")
        assert "tor_document" in data
        assert "message" in data
```

## 5. Cara Menjalankan

```bash
# Semua tests:
venv\Scripts\pytest tests/test_doc_style_integration.py -v --tb=short

# Hanya test active style:
venv\Scripts\pytest tests/test_doc_style_integration.py -v -k "TestActiveStyleUsed"

# Hanya test style_id parameter:
venv\Scripts\pytest tests/test_doc_style_integration.py -v -k "TestStyleIdParameter"
```

## 6. Acceptance Criteria

- [x] `pytest tests/test_doc_style_integration.py -v` → **semua test PASSED**.
- [x] Minimal 6 test cases.
- [x] Test bahwa active style digunakan secara default.
- [x] Test bahwa `post_processor.process()` menerima `style` parameter.
- [x] Test bahwa `style_id` spesifik berfungsi.
- [x] Test bahwa `style_id` invalid return 404.
- [x] Test backward compatibility (tanpa `style_id`).
- [x] Test response format tetap benar.
- [x] Tidak ada regresi pada test suite lain (`test_session_history.py`, `test_export_api.py`).
