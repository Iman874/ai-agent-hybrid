"""Unit tests RAG System — tidak membutuhkan Ollama."""
import pytest
from datetime import datetime
from app.models.rag import Document, DocumentMetadata, Chunk, ChunkMetadata, RetrievedChunk
from app.rag.document_loader import DocumentLoader
from app.rag.text_splitter import TextChunker
from app.rag.context_formatter import ContextFormatter
from app.utils.errors import UnsupportedFormatError


class TestDocumentLoader:
    loader = DocumentLoader()

    def test_load_from_upload_md(self):
        content = b"# Test TOR\n\n## Latar Belakang\nIni test.\n\n## Tujuan\nBelajar AI."
        doc = self.loader.load_from_upload("test.md", content, "tor_example")
        assert doc.metadata.source == "test.md"
        assert doc.metadata.category == "tor_example"
        assert doc.metadata.file_type == "md"
        assert len(doc.id) == 16

    def test_load_from_upload_txt(self):
        content = b"Ini file teks biasa untuk testing upload."
        doc = self.loader.load_from_upload("notes.txt", content, "guideline")
        assert doc.metadata.file_type == "txt"

    def test_load_unsupported_format(self):
        with pytest.raises(UnsupportedFormatError) as exc:
            self.loader.load_from_upload("proposal.pdf", b"%PDF...", "tor_example")
        assert exc.value.code == "E009"

    def test_document_id_deterministic(self):
        content = b"# Sama\n\nIsi sama persis."
        doc1 = self.loader.load_from_upload("file.md", content, "tor_example")
        doc2 = self.loader.load_from_upload("file.md", content, "tor_example")
        assert doc1.id == doc2.id

    def test_different_content_different_id(self):
        doc1 = self.loader.load_from_upload("a.md", b"# Content A", "tor_example")
        doc2 = self.loader.load_from_upload("a.md", b"# Content B yang beda", "tor_example")
        assert doc1.id != doc2.id


class TestTextChunker:
    chunker = TextChunker(chunk_size=300, chunk_overlap=30, min_chunk_size=50)

    def _make_doc(self, content: str) -> Document:
        return Document(
            id="testid1234567890"[:16],
            content=content,
            metadata=DocumentMetadata(
                source="test.md", category="tor_example", file_type="md",
                char_count=len(content), loaded_at=datetime.utcnow()
            )
        )

    def test_split_normal_document(self):
        content = (
            "# TOR Workshop\n\n## Latar Belakang\n"
            "Workshop ini diselenggarakan untuk meningkatkan kompetensi ASN "
            "dalam bidang teknologi informasi dan kecerdasan buatan.\n\n"
            "## Tujuan\nPeserta mampu menggunakan tools AI produktivitas.\n\n"
            "## Output\nSertifikat dan modul pelatihan digital."
        )
        doc = self._make_doc(content)
        chunks = self.chunker.split(doc)
        assert len(chunks) >= 1

    def test_chunk_id_format(self):
        doc = self._make_doc(
            "# Test\n\n## Latar Belakang\nIni adalah konten yang cukup panjang untuk jadi chunk. "
            "Kita perlu memastikan bahwa chunk memiliki ID yang benar dan sesuai format."
        )
        chunks = self.chunker.split(doc)
        for i, chunk in enumerate(chunks):
            assert chunk.id == f"{doc.id}_chunk_{i}"

    def test_chunk_metadata_complete(self):
        doc = self._make_doc(
            "# Test\n\n## Latar Belakang\nIni konten test untuk chunk metadata. "
            "Konten ini harus cukup panjang agar tidak terfilter oleh min_chunk_size."
        )
        chunks = self.chunker.split(doc)
        if chunks:
            assert chunks[0].metadata.source == "test.md"
            assert chunks[0].metadata.category == "tor_example"
            assert chunks[0].metadata.total_chunks == len(chunks)

    def test_short_document_returns_empty(self):
        doc = self._make_doc("Pendek.")
        chunks = self.chunker.split(doc)
        assert chunks == []

    def test_no_chunk_shorter_than_min(self):
        doc = self._make_doc(
            "# Judul\n\n" + ("Kalimat yang cukup panjang untuk menjadi chunk valid. " * 10)
        )
        chunks = self.chunker.split(doc)
        for chunk in chunks:
            assert len(chunk.text) >= 50


def _make_chunk(i: int, score: float, source: str = "tor.md") -> RetrievedChunk:
    return RetrievedChunk(
        id=f"chunk_{i}",
        text=f"Ini adalah konten referensi nomor {i} dari dokumen TOR workshop AI.",
        score=score,
        metadata=ChunkMetadata(
            source=source, category="tor_example", file_type="md",
            chunk_index=i, total_chunks=5, char_count=60,
            loaded_at=datetime.utcnow()
        )
    )


class TestContextFormatter:
    def test_format_single_chunk(self):
        chunks = [_make_chunk(1, 0.91)]
        result = ContextFormatter.format(chunks)
        assert result is not None
        assert "REFERENSI" in result
        assert "Referensi 1" in result
        assert "similarity: 0.91" in result

    def test_format_multiple_chunks(self):
        chunks = [_make_chunk(1, 0.91), _make_chunk(2, 0.85), _make_chunk(3, 0.74)]
        result = ContextFormatter.format(chunks)
        assert "Referensi 1" in result
        assert "Referensi 2" in result
        assert "Referensi 3" in result

    def test_format_empty_returns_none(self):
        result = ContextFormatter.format([])
        assert result is None

    def test_format_contains_header_and_footer(self):
        chunks = [_make_chunk(1, 0.88)]
        result = ContextFormatter.format(chunks)
        assert result.startswith("## REFERENSI")
        assert "Catatan:" in result
