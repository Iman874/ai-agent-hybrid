"""
Tests untuk Beta 0.1.12: Document Upload + Style Integration.
Integration test endpoint dan unit test PostProcessor.
"""
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.tor_style import TORStyle, TORSection, TORStyleConfig
from app.core.style_manager import StyleNotFoundError

pytestmark = pytest.mark.asyncio

DOC_TEXT = (
    "Ini adalah dokumen uji untuk memastikan parser menerima panjang minimal "
    "dan endpoint berjalan dengan benar. " * 2
).encode("utf-8")


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

    mock_style_mgr = MagicMock()
    mock_style_mgr.get_active_style.return_value = test_style

    def _get_style(style_id: str) -> TORStyle:
        if style_id == "custom_abc":
            return custom_style
        raise StyleNotFoundError(f"Style {style_id} not found")

    mock_style_mgr.get_style.side_effect = _get_style

    mock_gemini = AsyncMock()
    mock_gemini.model_name = "gemini-2.5-pro"
    mock_response = MagicMock()
    mock_response.text = "## Latar Belakang\n\nIni latar belakang test.\n\n## Tujuan\n\nIni tujuan test."
    mock_response.duration_ms = 1000
    mock_response.prompt_tokens = 100
    mock_response.completion_tokens = 200
    mock_gemini.generate.return_value = mock_response

    mock_pp = MagicMock()
    mock_processed = MagicMock()
    mock_processed.content = "## TOR Test\n\nKonten test."
    mock_processed.word_count = 50
    mock_processed.has_assumptions = False
    mock_pp.process.return_value = mock_processed

    mock_cache = AsyncMock()
    mock_cache.store = AsyncMock()

    app.state.gemini_provider = mock_gemini
    app.state.post_processor = mock_pp
    app.state.style_manager = mock_style_mgr
    app.state.rag_pipeline = None
    app.state.tor_cache = mock_cache

    @asynccontextmanager
    async def _no_lifespan(_app):
        yield

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _no_lifespan
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, mock_style_mgr, mock_pp
    finally:
        app.router.lifespan_context = original_lifespan


class TestActiveStyleUsed:
    async def test_uses_active_style_by_default(self, mock_app):
        """Endpoint harus menggunakan active style jika style_id tidak diberikan."""
        client, style_mgr, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", DOC_TEXT, "text/plain")},
            data={"context": "Test context"},
        )

        assert resp.status_code == 200
        style_mgr.get_active_style.assert_called_once()
        style_mgr.get_style.assert_not_called()

    async def test_post_processor_receives_style(self, mock_app):
        """PostProcessor.process() harus menerima style parameter."""
        client, style_mgr, post_proc = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", DOC_TEXT, "text/plain")},
            data={"context": ""},
        )

        assert resp.status_code == 200
        args, kwargs = post_proc.process.call_args
        if "style" in kwargs:
            assert kwargs["style"] == style_mgr.get_active_style.return_value
        else:
            assert len(args) > 1
            assert args[1] == style_mgr.get_active_style.return_value


class TestStyleIdParameter:
    async def test_specific_style_id(self, mock_app):
        """Endpoint harus menggunakan style spesifik jika style_id diberikan."""
        client, style_mgr, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", DOC_TEXT, "text/plain")},
            data={"context": "", "style_id": "custom_abc"},
        )

        assert resp.status_code == 200
        style_mgr.get_style.assert_called_once_with("custom_abc")
        style_mgr.get_active_style.assert_not_called()

    async def test_invalid_style_id_returns_404(self, mock_app):
        """style_id yang tidak ada harus return 404."""
        client, _, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", DOC_TEXT, "text/plain")},
            data={"context": "", "style_id": "tidak_ada"},
        )

        assert resp.status_code == 404

    async def test_no_style_id_backward_compatible(self, mock_app):
        """Tanpa style_id harus tetap berfungsi (backward compatible)."""
        client, _, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", DOC_TEXT, "text/plain")},
            data={"context": ""},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "tor_document" in data
        assert "session_id" in data


class TestResponseFormat:
    async def test_response_contains_tor_document(self, mock_app):
        """Response harus mengandung tor_document dan session_id."""
        client, _, _ = mock_app

        resp = await client.post(
            "/api/v1/generate/from-document",
            files={"file": ("test.txt", DOC_TEXT, "text/plain")},
            data={"context": "Buat TOR workshop."},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"].startswith("doc-")
        assert "tor_document" in data
        assert "message" in data
