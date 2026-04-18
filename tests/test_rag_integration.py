"""
Integration tests RAG System.
REQUIRES: Ollama running + qwen3-embedding:0.6b pulled
"""
import pytest
import pytest_asyncio
import os
import shutil

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def test_pipeline(tmp_path):
    """Setup RAGPipeline dengan temp ChromaDB path."""
    chroma_path = str(tmp_path / "test_chroma")
    os.environ["CHROMA_DB_PATH"] = chroma_path
    from app.config import Settings
    from app.rag.pipeline import RAGPipeline
    settings = Settings()
    settings.chroma_db_path = chroma_path
    pipeline = RAGPipeline(settings)
    yield pipeline
    shutil.rmtree(chroma_path, ignore_errors=True)


async def test_ingest_from_upload(test_pipeline):
    content = (
        b"# TOR Workshop AI\n\n"
        b"## Latar Belakang\nWorkshop ini diselenggarakan untuk mendukung transformasi digital.\n\n"
        b"## Tujuan\nMeningkatkan kompetensi ASN dalam bidang AI.\n\n"
        b"## Ruang Lingkup\nPelatihan 3 hari untuk 30 peserta ASN di Jakarta.\n\n"
        b"## Output\nSertifikat, modul pelatihan, dan laporan evaluasi.\n\n"
        b"## Timeline\nJuli 2026, tanggal 14-16 Juli 2026 di Balai Diklat."
    )
    result = await test_pipeline.ingest_from_uploads(
        uploads=[("test_tor.md", content)],
        category="tor_example"
    )
    assert result.ingested_files == 1
    assert result.total_chunks > 0
    assert result.details[0].status == "ingested"


async def test_retrieve_returns_context_or_none(test_pipeline):
    content = (
        b"# TOR Workshop Machine Learning\n\n"
        b"## Latar Belakang\nPeningkatan kapasitas SDM digital sangat diperlukan.\n\n"
        b"## Tujuan\nASN mampu menerapkan machine learning dalam analisis data.\n\n"
        b"## Output\nSertifikat dan laporan praktik."
    )
    await test_pipeline.ingest_from_uploads(
        uploads=[("tor_ml.md", content)], category="tor_example"
    )
    context = await test_pipeline.retrieve("workshop machine learning ASN")
    # Context bisa None jika score di bawah threshold, itu OK
    if context is not None:
        assert "REFERENSI" in context


async def test_get_status(test_pipeline):
    status = await test_pipeline.get_status()
    assert status["status"] == "healthy"
    assert "vector_db" in status
    assert "documents" in status
    assert status["vector_db"]["type"] == "chromadb"
