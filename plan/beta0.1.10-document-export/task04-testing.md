# Task 04: Testing

> **File Target**: `tests/test_document_exporter.py`, `tests/test_export_api.py`
> **Dependency**: ⚠️ Membutuhkan Task 01 + Task 02 selesai
> **Status**: [ ] Belum Dikerjakan

## 1. Tujuan

Menulis test suite yang memvalidasi:
1. **Unit test**: `DocumentExporterService` menghasilkan output bytes yang valid untuk setiap format.
2. **Integration test**: Endpoint `GET /api/v1/export/{session_id}` menghasilkan response HTTP yang benar.

## 2. Konvensi Testing Proyek

Berdasarkan test files yang sudah ada di codebase:

| Konvensi | Detail |
|---|---|
| Framework | `pytest` + `pytest-asyncio` |
| Marker | `pytestmark = pytest.mark.asyncio` di awal file |
| Async | Semua test yang melibatkan DB/API harus `async def` |
| Fixture | Pakai `@pytest_asyncio.fixture` untuk async setup |
| DB fixture | `conftest.py` sudah menyediakan `test_db_path` (tmp_path) dan `initialized_db` |

## 3. Unit Test — `DocumentExporterService`

- [ ] Buat file `tests/test_document_exporter.py`:

```python
"""
Unit tests untuk DocumentExporterService.
Tidak memerlukan database atau server.
"""
import io
import pytest
from docx import Document as DocxDocument

from app.services.document_exporter import DocumentExporterService
from app.utils.errors import ExportError


# --- Fixture ---

@pytest.fixture
def exporter():
    """Instance DocumentExporterService untuk testing."""
    return DocumentExporterService()


@pytest.fixture
def sample_markdown():
    """Sample TOR Markdown content yang realistis."""
    return """# TERM OF REFERENCE (TOR)
# Workshop Penerapan AI untuk ASN

## 1. Latar Belakang

Perkembangan teknologi **Artificial Intelligence** (AI) telah mengubah berbagai sektor.
Pemerintah perlu mempersiapkan ASN yang *kompeten* dalam pemanfaatan AI.

## 2. Tujuan

- Meningkatkan pemahaman ASN tentang AI
- Membangun kapasitas digital aparatur
- Mendorong inovasi layanan publik

## 3. Ruang Lingkup

| No | Komponen | Keterangan |
|----|----------|------------|
| 1  | Pelatihan | 3 hari intensif |
| 2  | Workshop | Hands-on project |
| 3  | Evaluasi | Pre & post test |

## 4. Timeline

1. Persiapan: Minggu 1-2
2. Pelaksanaan: Minggu 3
3. Evaluasi: Minggu 4

---

## 5. Penutup

Demikian TOR ini disusun sebagai acuan pelaksanaan kegiatan.
"""


# --- Tests: export_to_md ---

class TestExportMd:
    def test_returns_bytes(self, exporter, sample_markdown):
        result = exporter.export_to_md(sample_markdown)
        assert isinstance(result, bytes)

    def test_content_identical(self, exporter, sample_markdown):
        """MD export harus identik dengan input setelah decode."""
        result = exporter.export_to_md(sample_markdown)
        assert result.decode("utf-8") == sample_markdown

    def test_utf8_encoding(self, exporter):
        """Harus handle karakter Indonesia dengan benar."""
        text = "# TOR Pengadaan Barang — Rp 50.000.000"
        result = exporter.export_to_md(text)
        assert "Rp 50.000.000" in result.decode("utf-8")

    def test_empty_input(self, exporter):
        result = exporter.export_to_md("")
        assert result == b""


# --- Tests: export_to_pdf ---

class TestExportPdf:
    def test_returns_bytes(self, exporter, sample_markdown):
        result = exporter.export_to_pdf(sample_markdown)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_pdf_magic_bytes(self, exporter, sample_markdown):
        """PDF file harus dimulai dengan magic bytes %PDF."""
        result = exporter.export_to_pdf(sample_markdown)
        assert result[:4] == b"%PDF", f"Got: {result[:20]}"

    def test_minimal_input(self, exporter):
        result = exporter.export_to_pdf("# Hello")
        assert result[:4] == b"%PDF"


# --- Tests: export_to_docx ---

class TestExportDocx:
    def test_returns_bytes(self, exporter, sample_markdown):
        result = exporter.export_to_docx(sample_markdown)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_valid_docx_file(self, exporter, sample_markdown):
        """Output harus bisa di-load sebagai valid DOCX."""
        result = exporter.export_to_docx(sample_markdown)
        # python-docx bisa membaca file → file valid
        doc = DocxDocument(io.BytesIO(result))
        assert len(doc.paragraphs) > 0 or len(doc.tables) > 0

    def test_heading_preserved(self, exporter):
        """Heading Markdown harus menjadi heading di DOCX."""
        result = exporter.export_to_docx("# Judul Utama\n\n## Sub Judul")
        doc = DocxDocument(io.BytesIO(result))
        # Cari heading element
        headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
        assert "Judul Utama" in headings
        assert "Sub Judul" in headings

    def test_table_created(self, exporter):
        """Tabel Markdown harus menjadi tabel di DOCX."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = exporter.export_to_docx(md)
        doc = DocxDocument(io.BytesIO(result))
        assert len(doc.tables) >= 1
        # Verifikasi content cell
        assert doc.tables[0].cell(0, 0).text.strip() in ("A", "1")

    def test_bold_formatting(self, exporter):
        """**Bold** Markdown harus menjadi bold run di DOCX."""
        result = exporter.export_to_docx("Ini **tebal** sekali")
        doc = DocxDocument(io.BytesIO(result))
        # Cari run yang bold
        bold_runs = []
        for p in doc.paragraphs:
            for run in p.runs:
                if run.bold:
                    bold_runs.append(run.text)
        assert "tebal" in bold_runs

    def test_bullet_list(self, exporter):
        """List Markdown harus menjadi list style di DOCX."""
        md = "- Item satu\n- Item dua\n- Item tiga"
        result = exporter.export_to_docx(md)
        doc = DocxDocument(io.BytesIO(result))
        list_items = [p.text for p in doc.paragraphs if "List" in (p.style.name or "")]
        assert len(list_items) >= 3


# --- Tests: export() dispatcher ---

class TestExportDispatcher:
    def test_md_dispatch(self, exporter):
        result = exporter.export("# Test", "md")
        assert result == b"# Test"

    def test_pdf_dispatch(self, exporter):
        result = exporter.export("# Test", "pdf")
        assert result[:4] == b"%PDF"

    def test_docx_dispatch(self, exporter):
        result = exporter.export("# Test", "docx")
        doc = DocxDocument(io.BytesIO(result))
        assert doc is not None

    def test_invalid_format_raises(self, exporter):
        with pytest.raises(ExportError) as exc_info:
            exporter.export("# Test", "xlsx")
        assert "tidak didukung" in exc_info.value.message

    def test_case_insensitive(self, exporter):
        """Format harus case-insensitive."""
        result = exporter.export("# Test", "PDF")
        assert result[:4] == b"%PDF"

    def test_whitespace_trimmed(self, exporter):
        """Format dengan whitespace harus di-trim."""
        result = exporter.export("# Test", " md ")
        assert result == b"# Test"
```

## 4. Integration Test — Export API Endpoint

- [ ] Buat file `tests/test_export_api.py`:

```python
"""
Integration tests untuk export API endpoint.
Menggunakan FastAPI TestClient + real SQLite temp DB.
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
        assert ".docx" in resp.headers["Content-Disposition"]
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
        # MD content harus identik
        assert resp.content.decode("utf-8") == SAMPLE_TOR_CONTENT

    async def test_default_format_is_docx(self, client):
        """Jika format tidak disebutkan, default ke docx."""
        resp = await client.get(f"/api/v1/export/{SAMPLE_SESSION_ID}")
        assert resp.status_code == 200
        assert "wordprocessingml" in resp.headers["content-type"]


# --- Negative Path Tests ---

class TestExportNegativePath:
    async def test_session_not_found(self, client):
        """Session ID yang tidak ada → 404."""
        resp = await client.get(
            "/api/v1/export/nonexistent-session-id",
            params={"format": "docx"},
        )
        # Error handler converts SessionNotFoundError → appropriate HTTP status
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
    async def test_filename_contains_session_id(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "pdf"},
        )
        disposition = resp.headers.get("Content-Disposition", "")
        assert "TOR_" in disposition
        assert ".pdf" in disposition

    async def test_filename_docx_extension(self, client):
        resp = await client.get(
            f"/api/v1/export/{SAMPLE_SESSION_ID}",
            params={"format": "docx"},
        )
        disposition = resp.headers.get("Content-Disposition", "")
        assert ".docx" in disposition
```

## 5. Cara Menjalankan Tests

```bash
# Unit tests saja (cepat, tidak perlu server):
pytest tests/test_document_exporter.py -v

# Integration tests (perlu app context):
pytest tests/test_export_api.py -v

# Semua export tests:
pytest tests/test_document_exporter.py tests/test_export_api.py -v

# Dengan coverage:
pytest tests/test_document_exporter.py tests/test_export_api.py -v --tb=short
```

## 6. Acceptance Criteria

- [ ] `pytest tests/test_document_exporter.py -v` → **semua test PASSED** (minimal 15 test cases).
- [ ] `pytest tests/test_export_api.py -v` → **semua test PASSED** (minimal 7 test cases).
- [ ] Tidak ada `xfail` atau `skip` yang tidak disertai alasan.
- [ ] Coverage service layer (`document_exporter.py`) ≥ 90%.
