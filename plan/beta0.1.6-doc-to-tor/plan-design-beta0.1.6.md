# 📄 Plan Design — Beta 0.1.6: Document-to-TOR Generator
# AI Agent Hybrid — Gemini Document Processing

> **Modul**: Document-to-TOR (Generate TOR dari Dokumen Upload)
> **Versi**: beta0.1.6
> **Status**: Plan Ready
> **Prasyarat**: beta0.1.5 selesai (Streamlit UI + Gemini Direct sudah ada)

---

## 1. Ringkasan Modul

Fitur ini memungkinkan user **mengupload dokumen** (PDF, TXT, DOCX, MD) dan **otomatis generate TOR** berdasarkan isi dokumen tersebut via Gemini API. Ini berbeda dari RAG yang berfungsi sebagai referensi style — ini menjadikan dokumen user sebagai **sumber data utama**.

### Contoh Use Case

| Dokumen Input | Output |
|---|---|
| Laporan kegiatan tahun lalu | TOR kegiatan lanjutan tahun ini |
| Notulen rapat perencanaan | TOR formal berdasarkan hasil rapat |
| Proposal kegiatan draft | TOR lengkap yang dirapikan dari proposal |
| Dokumen kebijakan | TOR implementasi kebijakan |

### Kenapa Gemini Only?

| Alasan | Detail |
|---|---|
| **Context window** | Dokumen bisa 10-50 halaman, butuh context window besar |
| **Reasoning** | Mengekstrak structured data dari dokumen unstructured butuh reasoning tingkat tinggi |
| **Bahasa** | Gemini comprehension Bahasa Indonesia jauh lebih baik dari local 7B LLM |
| **Speed** | Gemini Flash bisa proses dokumen panjang dalam detik |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    streamlit_app.py                       │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Tab: 📄 From Document                            │   │
│  │                                                    │   │
│  │  [📎 Upload PDF/TXT/MD/DOCX]  ← st.file_uploader │   │
│  │  [Konteks tambahan...]         ← st.text_area     │   │
│  │  [🚀 Generate TOR dari Dokumen]                   │   │
│  │                                                    │   │
│  │  --- TOR Preview + Download ---                   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP POST (multipart/form-data)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                              │
│                                                          │
│  POST /api/v1/generate/from-document                     │
│    │                                                     │
│    ├── 1. Extract text dari file                         │
│    │      ├── PDF → pypdf / pdfplumber                   │
│    │      ├── DOCX → python-docx                         │
│    │      └── TXT/MD → langsung baca                     │
│    │                                                     │
│    ├── 2. Build prompt (document-to-TOR)                 │
│    │      ├── System: "Kamu adalah pembuat TOR..."       │
│    │      ├── Document text (full content)               │
│    │      ├── Konteks tambahan user                      │
│    │      └── RAG examples (optional, style reference)   │
│    │                                                     │
│    ├── 3. Gemini API call                                │
│    │                                                     │
│    ├── 4. Post-process TOR                               │
│    │                                                     │
│    └── 5. Return TOR + metadata                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Komponen Baru

### 3.1 Backend

| File | Tipe | Deskripsi |
|---|---|---|
| `app/core/document_parser.py` | **NEW** | Ekstrak teks dari PDF/TXT/MD/DOCX |
| `app/ai/prompts/document_tor.py` | **NEW** | Prompt template untuk document-to-TOR |
| `app/api/routes/generate_doc.py` | **NEW** | Endpoint `POST /api/v1/generate/from-document` |
| `app/api/router.py` | **MODIFY** | Register route baru |
| `requirements.txt` | **MODIFY** | Tambah `pypdf`, `python-docx` |

### 3.2 Frontend

| File | Tipe | Deskripsi |
|---|---|---|
| `streamlit_app.py` | **MODIFY** | Tambah tab ke-3: "📄 From Document" |

---

## 4. Detail Teknis

### 4.1 Document Parser

```python
# app/core/document_parser.py

class DocumentParser:
    """Ekstrak teks dari berbagai format dokumen."""

    SUPPORTED_FORMATS = [".pdf", ".txt", ".md", ".docx"]
    MAX_FILE_SIZE_MB = 20

    @staticmethod
    async def parse(file_bytes: bytes, filename: str) -> str:
        """Parse file bytes → plain text."""
        ext = Path(filename).suffix.lower()

        if ext in (".txt", ".md"):
            return file_bytes.decode("utf-8")
        elif ext == ".pdf":
            return DocumentParser._parse_pdf(file_bytes)
        elif ext == ".docx":
            return DocumentParser._parse_docx(file_bytes)
        else:
            raise ValueError(f"Format tidak didukung: {ext}")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        """Extract text dari PDF via pypdf."""
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        """Extract text dari DOCX via python-docx."""
        from docx import Document
        import io
        doc = Document(io.BytesIO(file_bytes))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
```

### 4.2 Prompt Template

```python
# app/ai/prompts/document_tor.py

DOCUMENT_TO_TOR_PROMPT = """
# INSTRUKSI
Kamu adalah pembuat dokumen TOR (Term of Reference) profesional pemerintah Indonesia.

Berdasarkan dokumen yang diberikan di bawah, buat TOR yang lengkap dan formal.

## TUGAS
1. Baca dan pahami dokumen sumber secara menyeluruh
2. Ekstrak informasi relevan: tujuan, latar belakang, ruang lingkup, timeline, dll
3. Susun TOR dalam format standar pemerintah Indonesia
4. Jika ada informasi yang kurang di dokumen, berikan catatan [ASUMSI]

## KONTEKS TAMBAHAN DARI USER
{USER_CONTEXT}

## DOKUMEN SUMBER
---
{DOCUMENT_TEXT}
---

{RAG_EXAMPLES}

## FORMAT OUTPUT
TOR harus dalam format Markdown dengan struktur:
- Judul/Nama Kegiatan
- Latar Belakang
- Tujuan (Umum dan Khusus)
- Ruang Lingkup
- Sasaran/Target
- Output/Deliverable
- Timeline/Jadwal
- Anggaran (jika disebutkan di dokumen)
- Penutup

Tulis dalam Bahasa Indonesia formal, gunakan kosakata pemerintah yang baku.
"""
```

### 4.3 API Endpoint

```python
# app/api/routes/generate_doc.py

@router.post("/generate/from-document")
async def generate_from_document(
    request: Request,
    file: UploadFile = File(...),
    context: str = Form(""),
):
    """Generate TOR dari dokumen upload."""
    # 1. Validate file
    # 2. Parse document → text
    # 3. Build prompt (document + context + RAG)
    # 4. Call Gemini
    # 5. Post-process
    # 6. Return TOR
```

### 4.4 Streamlit Tab

```
Tab: 📄 From Document
┌──────────────────────────────────────┐
│  📄 Generate TOR dari Dokumen        │
│  Upload dokumen, Gemini baca &       │
│  buatkan TOR secara otomatis.        │
│                                       │
│  Format: PDF, TXT, MD, DOCX          │
│  Maks: 20MB                          │
│                                       │
│  [📎 Drag & drop atau browse...]     │  ← st.file_uploader
│  ✅ laporan_kegiatan_2025.pdf (2.3MB)│
│                                       │
│  Konteks tambahan (opsional):         │
│  [Ini lanjutan workshop tahun lalu,  ]│  ← st.text_area
│  [target peserta sama tapi materi    ]│
│  [ditingkatkan ke level advanced.    ]│
│                                       │
│  [🚀 Generate TOR dari Dokumen]      │
│                                       │
│  --- TOR Preview ---                  │
│  ✅ TOR Berhasil Dibuat!              │
│  📋 Metadata: model, words, time     │
│  📄 Preview rendered markdown         │
│  [⬇️ Download TOR (.md)]             │
│                                       │
└──────────────────────────────────────┘
```

---

## 5. Flow Lengkap

```
User:
  1. Klik tab "📄 From Document"
  2. Upload file PDF (laporan kegiatan 2025)
  3. Tulis konteks: "Buat TOR lanjutan di 2026"
  4. Klik "🚀 Generate TOR dari Dokumen"

Backend:
  1. Terima file → DocumentParser.parse() → plain text
  2. Build prompt: DOCUMENT_TO_TOR_PROMPT + document_text + context
  3. (Optional) RAG retrieve untuk style reference
  4. Gemini API call → raw TOR text
  5. PostProcessor.process() → clean TOR
  6. Return GenerateResponse

Frontend:
  1. Tampilkan TOR preview (rendered markdown)
  2. Metadata: model, word count, generation time
  3. Download button .md
```

---

## 6. Error Handling

| Error | Handling |
|---|---|
| File terlalu besar (>20MB) | 400: "File exceeds maximum size" |
| Format tidak didukung | 400: "Unsupported file format" |
| PDF tidak bisa di-parse (scanned/image) | 400: "Tidak bisa ekstrak teks dari PDF ini" |
| Teks terlalu pendek (<50 chars) | 400: "Dokumen terlalu pendek" |
| Gemini timeout | 504: retry + user notification |
| Gemini rate limit | 429: retry_after |

---

## 7. Dependencies Baru

```
# requirements.txt — tambahan
pypdf>=4.0                    # PDF text extraction
python-docx>=1.0              # DOCX text extraction
```

---

## 8. Batasan & Catatan

| Item | Detail |
|---|---|
| **Scanned PDF** | TIDAK didukung (image-based PDF). Hanya text-based PDF. |
| **OCR** | Ditunda ke v1.0. Bisa pakai Gemini Vision nanti. |
| **File storage** | File TIDAK disimpan di server. Diproses langsung, lalu dibuang. |
| **Token limit** | Gemini Flash ~1M tokens. Cukup untuk ~3000 halaman teks. |
| **Session** | Document-to-TOR TIDAK membuat session. Stateless one-shot. |

---

## 9. Task Breakdown

| # | Task | Deskripsi | Estimasi |
|---|---|---|---|
| 1 | `task01-document-parser.md` | Buat `DocumentParser` (PDF, TXT, MD, DOCX) + install deps | Medium |
| 2 | `task02-prompt-template.md` | Buat prompt template `DOCUMENT_TO_TOR_PROMPT` | Low |
| 3 | `task03-api-endpoint.md` | Buat endpoint `POST /api/v1/generate/from-document` | Medium |
| 4 | `task04-streamlit-tab.md` | Tambah tab "📄 From Document" di Streamlit | Medium |
| 5 | `task05-testing.md` | Manual testing: upload PDF, TXT, error cases | Medium |
| 6 | `task09-pdf-export.md` | Tambah fitur download TOR sebagai PDF di UI Streamlit (seluruh tab) | Low |

---

## 10. Hubungan dengan RAG

```
RAG Pipeline (sudah ada):
  data/documents/ ─ingest─► ChromaDB ─retrieve─► style examples untuk prompt
                                                    ↓
Document-to-TOR (baru):                       inject ke prompt
  user upload file ─parse─► raw text ─────────► Gemini prompt
                                                    ↓
                                              Generated TOR
```

RAG tetap berfungsi sebagai **referensi style** — contoh TOR yang bagus disisipkan ke prompt agar Gemini tahu format yang diharapkan. Dokumen user adalah **sumber data**, RAG adalah **sumber gaya penulisan**.

---

> **Modul ini independen dan tidak mengubah flow Hybrid atau Gemini Direct yang sudah ada.** Implementasi cukup menambah 1 endpoint + 1 tab + 1 parser.
