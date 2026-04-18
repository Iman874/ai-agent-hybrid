# Task 13 — Sample Documents & Integration Test

## 1. Judul Task

Buat dokumen contoh TOR (template, example, guideline) dan jalankan integration test end-to-end RAG pipeline.

## 2. Deskripsi

Membuat 3+ dokumen contoh yang realistis di `data/documents/` (template TOR workshop, contoh TOR yang sudah jadi, panduan bahasa formal), lalu menjalankan test `pytest` untuk memverifikasi full RAG pipeline: ingest → retrieve → format context. Test tidak membutuhkan Ollama aktif untuk unit test komponen, tapi membutuhkan Ollama + bge-m3 untuk integration test.

## 3. Tujuan Teknis

- Test suite `pytest tests/test_rag_*.py` bisa dijalankan
- Unit test: DocumentLoader, TextChunker, ContextFormatter (tanpa Ollama)
- Integration test: full pipeline ingest + retrieve (butuh Ollama + bge-m3)
- Sample documents yang realistis tersedia di `data/documents/`

## 4. Scope

### Yang dikerjakan
- `data/documents/templates/template_tor_workshop.md`
- `data/documents/examples/tor_workshop_ai_2025.md`
- `data/documents/guidelines/guideline_bahasa_formal.md`
- `tests/test_rag_unit.py` — unit tests (tanpa Ollama)
- `tests/test_rag_integration.py` — integration test (dengan Ollama)

### Yang tidak dikerjakan
- Test dengan model LLM (itu test manual di beta0.1.1)
- Performance testing

## 5. Langkah Implementasi

### Step 1: Buat `data/documents/templates/template_tor_workshop.md`

```markdown
# Template: Kerangka Acuan Kerja (KAK) Workshop / Pelatihan

**[NAMA INSTANSI]**
**[TAHUN ANGGARAN]**

---

## I. Latar Belakang

[Deskripsikan konteks dan alasan mengapa kegiatan ini perlu dilakukan.
Sertakan kondisi terkini, permasalahan yang dihadapi, dan relevansinya
dengan program kerja instansi.]

## II. Tujuan

Kegiatan ini bertujuan untuk:

1. [Tujuan pertama — gunakan kata kerja aktif]
2. [Tujuan kedua]
3. [Tujuan ketiga]

## III. Ruang Lingkup

Kegiatan ini mencakup:

* **Peserta**: [Jumlah dan kriteria peserta]
* **Lokasi**: [Kota/Venue pelaksanaan]
* **Durasi**: [Total hari dan jam pelajaran]
* **Materi**: [Topik-topik yang akan dibahas]

## IV. Output / Keluaran

Keluaran yang diharapkan dari kegiatan ini adalah:

1. [Output 1, misalnya: Sertifikat kehadiran]
2. [Output 2, misalnya: Modul pelatihan]
3. [Output 3, misalnya: Laporan evaluasi]

## V. Timeline / Jadwal Pelaksanaan

| Kegiatan | Waktu |
|---|---|
| Persiapan | [Tanggal] |
| Pelaksanaan Workshop | [Tanggal] |
| Evaluasi & Laporan | [Tanggal] |

## VI. Estimasi Biaya (Opsional)

Total estimasi biaya: Rp [Jumlah]
```

### Step 2: Buat `data/documents/examples/tor_workshop_ai_2025.md`

```markdown
# Kerangka Acuan Kerja
# Workshop Penerapan Kecerdasan Buatan (AI) untuk ASN
# Badan Kepegawaian dan Pengembangan SDM Provinsi X
# Tahun Anggaran 2025

---

## I. Latar Belakang

Perkembangan teknologi kecerdasan buatan (AI) yang pesat membawa perubahan
signifikan dalam berbagai sektor, termasuk pelayanan publik.

Berdasarkan survei internal, 78% ASN di lingkungan Provinsi X belum pernah
mendapatkan pelatihan formal terkait pemanfaatan AI dalam pekerjaan.

## II. Tujuan

1. Meningkatkan pemahaman ASN tentang konsep dasar dan aplikasi AI generatif
2. Membekali peserta dengan kemampuan menggunakan tools AI produktivitas
3. Mendorong adopsi AI dalam proses kerja sehari-hari

## III. Ruang Lingkup

* **Peserta**: 30 orang ASN dari semua OPD
* **Lokasi**: Aula Badan Diklat Provinsi X
* **Durasi**: 3 hari kerja (24 jam pelajaran)
* **Metode**: Ceramah, praktik, diskusi kelompok

## IV. Output

1. Sertifikat kehadiran untuk 30 peserta
2. Modul pelatihan digital dalam format PDF
3. Laporan pelaksanaan kegiatan
4. Rencana aksi implementasi AI dari masing-masing OPD

## V. Timeline

| Kegiatan | Tanggal |
|---|---|
| Persiapan | 1 - 10 Juli 2025 |
| Pelaksanaan workshop | 14 - 16 Juli 2025 |
| Pelaporan | 25 Juli 2025 |

## VI. Estimasi Biaya

Total: **Rp 75.000.000,-**

- Honorarium narasumber: Rp 18.000.000
- Sewa venue: Rp 15.000.000
- Konsumsi peserta: Rp 13.500.000
- Materi pelatihan: Rp 8.500.000
- Transportasi: Rp 12.000.000
- Dokumentasi: Rp 8.000.000
```

### Step 3: Buat `data/documents/guidelines/guideline_bahasa_formal.md`

```markdown
# Panduan Penulisan Dokumen KAK / TOR dalam Bahasa Indonesia Formal

## 1. Ketentuan Umum

Dokumen KAK (Kerangka Acuan Kerja) harus ditulis menggunakan Bahasa Indonesia
yang baku sesuai KBBI dan EYD.

## 2. Gaya Bahasa

- Gunakan kalimat **aktif** dan **efektif**
- Hindari kata-kata klise dan basa-basi berlebihan
- Setiap paragraf maksimal 5-7 kalimat

## 3. Format Angka dan Satuan

- Angka 1-9: ditulis dengan huruf ("satu", "tiga")
- Angka 10 ke atas: boleh ditulis angka (10, 250)
- Pecahan uang: tulis angka dan huruf ("Rp 5.000.000,- (Lima juta rupiah)")

## 4. Struktur Kalimat yang Dianjurkan

Untuk bagian Tujuan, gunakan kata kerja aktif infinitif:
"Meningkatkan / Membekali / Mendorong / Membentuk / Menghasilkan"

Untuk bagian Output, gunakan kata benda konkret:
"Laporan / Sertifikat / Modul / Prototype / Rekomendasi"

## 5. Hal yang Harus Dihindari

- Penggunaan bahasa Inggris yang berlebihan tanpa alasan
- Kalimat pasif yang membingungkan
- Singkatan yang tidak dijelaskan saat pertama kali disebutkan
- Data atau angka tanpa sumber yang jelas
```

### Step 4: Buat `tests/test_rag_unit.py`

```python
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
            "# Test\n\n## Latar Belakang\nIni adalah konten yang cukup panjang untuk jadi chunk."
        )
        chunks = self.chunker.split(doc)
        for i, chunk in enumerate(chunks):
            assert chunk.id == f"{doc.id}_chunk_{i}"

    def test_chunk_metadata_complete(self):
        doc = self._make_doc(
            "# Test\n\n## Latar Belakang\nIni konten test untuk chunk metadata."
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
            "# Judul\n\n" + ("Kalimat yang cukup panjang untuk menjadi chunk valid. " * 5)
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
```

### Step 5: Buat `tests/test_rag_integration.py`

```python
"""
Integration tests RAG System.
REQUIRES: Ollama running + bge-m3 pulled
"""
import pytest
import os
import shutil

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def test_pipeline(tmp_path):
    """Setup RAGPipeline dengan temp ChromaDB path."""
    os.environ["CHROMA_DB_PATH"] = str(tmp_path / "test_chroma")
    from app.config import Settings
    from app.rag.pipeline import RAGPipeline
    settings = Settings()
    pipeline = RAGPipeline(settings)
    yield pipeline
    shutil.rmtree(str(tmp_path / "test_chroma"), ignore_errors=True)


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
    if context is not None:
        assert "REFERENSI" in context


async def test_get_status(test_pipeline):
    status = await test_pipeline.get_status()
    assert status["status"] == "healthy"
    assert "vector_db" in status
    assert "documents" in status
    assert status["vector_db"]["type"] == "chromadb"
```

### Step 6: Jalankan tests

```bash
# Unit tests (tanpa Ollama)
.\venv\Scripts\pytest.exe tests/test_rag_unit.py -v

# Integration test (butuh Ollama + bge-m3)
.\venv\Scripts\pytest.exe tests/test_rag_integration.py -v
```

## 6. Output yang Diharapkan

```
tests/test_rag_unit.py::TestDocumentLoader::test_load_from_upload_md PASSED
tests/test_rag_unit.py::TestDocumentLoader::test_load_unsupported_format PASSED
tests/test_rag_unit.py::TestDocumentLoader::test_document_id_deterministic PASSED
tests/test_rag_unit.py::TestTextChunker::test_split_normal_document PASSED
tests/test_rag_unit.py::TestTextChunker::test_chunk_id_format PASSED
tests/test_rag_unit.py::TestTextChunker::test_short_document_returns_empty PASSED
tests/test_rag_unit.py::TestContextFormatter::test_format_single_chunk PASSED
tests/test_rag_unit.py::TestContextFormatter::test_format_empty_returns_none PASSED
...
====================== 14 passed in X.XXs ======================
```

## 7. Dependencies

- **Semua task sebelumnya (01–12)** harus selesai
- `pytest-asyncio` sudah terinstall (dari beta0.1.0)
- External (untuk integration test): Ollama + bge-m3

## 8. Acceptance Criteria

- [ ] 3 file contoh dokumen ada di `data/documents/` (templates, examples, guidelines)
- [ ] `pytest tests/test_rag_unit.py -v` → 14 tests PASSED tanpa Ollama
- [ ] `pytest tests/test_rag_integration.py -v` → semua PASSED dengan Ollama + bge-m3
- [ ] `python scripts/ingest_documents.py --dir data/documents/examples --category tor_example` berhasil
- [ ] `GET /api/v1/rag/status` setelah ingest menampilkan dokumen yang sudah di-index

## 9. Estimasi

**Medium** — ~2 jam
