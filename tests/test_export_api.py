"""
Integration tests untuk export API endpoint.
Menggunakan httpx AsyncClient + real SQLite temp DB.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import init_db
from app.db.repositories.cache_repo import TORCache
from app.models.generate import TORDocument, TORMetadata

pytestmark = pytest.mark.asyncio

# --- Constant ---
SAMPLE_SESSION_ID = "test-export-session-001"
SAMPLE_TOR_CONTENT = """# TERM OF REFERENCE
## Workshop AI

### 1. Latar Belakang
Kegiatan ini bertujuan meningkatkan kompetensi digital.

### 2. Tujuan
- Pemahaman dasar AI
- Implementasi use case
"""


@pytest_asyncio.fixture
async def seeded_app(tmp_path):
    """Setup app dengan TOR ter-cache di temp DB."""
    test_db = str(tmp_path / "test_export.db")
    await init_db(test_db)

    # Seed cache dengan dummy TOR
    cache = TORCache(test_db)
    tor_doc = TORDocument(
        content=SAMPLE_TOR_CONTENT,
        metadata=TORMetadata(
            generated_by="gemini-2.0-flash",
            mode="standard",
            word_count=42,
            generation_time_ms=1500,
        ),
    )
    await cache.store(SAMPLE_SESSION_ID, tor_doc)

    # Override app.state untuk test
    app.state.tor_cache = cache

    from app.services.document_exporter import DocumentExporterService
    app.state.document_exporter = DocumentExporterService()

    yield app


@pytest_asyncio.fixture
async def client(seeded_app):
    """Async HTTP client untuk testing."""
    transport = ASGITransport(app=seeded_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Happy Path Tests ---

class TestExportHappyPath:
    async def test_export_docx(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "docx"},
        )
        assert resp.status_code == 200
        assert "wordprocessingml" in resp.headers["content-type"]
        assert "Content-Disposition" in resp.headers
        assert ".docx" in resp.headers["content-disposition"]
        assert len(resp.content) > 0

    async def test_export_pdf(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "pdf"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    async def test_export_md(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "md"},
        )
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]
        assert resp.content.decode("utf-8") == SAMPLE_TOR_CONTENT

    async def test_default_format_is_docx(self, client):
        """Jika format tidak disebutkan, default ke docx."""
        resp = await client.get(f"/api/v1/export/{SAMPLE_SESSION_ID}")
        assert resp.status_code == 200
        assert "wordprocessingml" in resp.headers["content-type"]


# --- Negative Path Tests ---

class TestExportNegativePath:
    async def test_session_not_found(self, client):
        """Session ID yang tidak ada harus gagal."""
        resp = await client.get(
            "/api/v1/export/nonexistent-session-id",
            params={"format": "docx"},
        )
        # SessionNotFoundError → mapped to 4xx or 5xx by error handler
        assert resp.status_code in (404, 500)

    async def test_invalid_format(self, client):
        """Format yang tidak valid → 422 (FastAPI validation)."""
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "xlsx"},
        )
        assert resp.status_code == 422


# --- Content-Disposition Tests ---

class TestContentDisposition:
    async def test_filename_contains_session_prefix(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "pdf"},
        )
        disposition = resp.headers.get("content-disposition", "")
        assert "TOR_" in disposition
        assert ".pdf" in disposition

    async def test_filename_docx_extension(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "docx"},
        )
        disposition = resp.headers.get("content-disposition", "")
        assert ".docx" in disposition
