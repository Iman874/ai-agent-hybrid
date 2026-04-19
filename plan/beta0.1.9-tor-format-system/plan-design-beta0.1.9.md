# 📘 Plan Design — Beta 0.1.9
# Customizable TOR Format System

> **Codename**: `tor-format-engine`
> **Versi**: Beta 0.1.9
> **Tanggal**: 2026-04-19
> **Status**: Draft — Menunggu Review
> **Prasyarat**: Beta 0.1.8 (Modular UI) selesai

---

## 1. Executive Summary

### 1.1 Masalah Saat Ini

Saat ini, format dan struktur dokumen TOR **di-hardcode** di dalam 3 file prompt backend:

| File | Format yang Terkunci |
|---|---|
| `app/ai/prompts/generate_tor.py` | Seksi 1–7, urutan tetap, gaya bahasa tetap |
| `app/ai/prompts/escalation.py` | Seksi 1–7 identik, mode asumsi |
| `app/ai/prompts/document_tor.py` | Seksi 1–8 (sedikit beda), gaya birokrasi tetap |

**Konsekuensi:**
- User tidak bisa mengubah urutan bab, nama seksi, atau gaya penulisan
- Semua TOR yang dihasilkan memiliki format identik
- Jika user memiliki contoh TOR referensi, tidak ada cara untuk "meniru" formatnya
- Menambah variasi format berarti developer harus mengedit kode Python

### 1.2 Solusi

Membangun **TOR Format Engine** — sebuah sistem yang memungkinkan user:

1. Melihat dan memahami format default yang digunakan sistem
2. Membuat format kustom baru ("style") dengan mendefinisikan seksi, urutan, gaya bahasa, dan kedalaman
3. Mengupload dokumen TOR referensi → sistem mengekstrak struktur dan gayanya secara otomatis menggunakan AI
4. Menyimpan multiple styles dan memilih salah satu sebagai format aktif
5. Format aktif berlaku **global** — digunakan oleh Chat, Gemini Direct, dan Dari Dokumen

---

## 2. Arsitektur Sistem

### 2.1 Alur Data End-to-End

```
┌─────────────────────────────────────┐
│         STREAMLIT UI                │
│                                     │
│  ┌─────────────────────────────┐   │
│  │   Tab: Format TOR           │   │
│  │                             │   │
│  │  ┌───────┐  ┌────────────┐ │   │
│  │  │Default│  │Custom Style│ │   │
│  │  │(locked)│  │  Manager   │ │   │
│  │  └───────┘  └─────┬──────┘ │   │
│  │                    │        │   │
│  │  ┌─────────────────▼──────┐ │   │
│  │  │ Style Editor           │ │   │
│  │  │ - Nama & deskripsi     │ │   │
│  │  │ - Seksi (add/del/sort) │ │   │
│  │  │ - Gaya bahasa          │ │   │
│  │  │ - Kedalaman konten     │ │   │
│  │  │ - Instruksi khusus     │ │   │
│  │  └────────────────────────┘ │   │
│  │                             │   │
│  │  ┌────────────────────────┐ │   │
│  │  │ Upload TOR Referensi   │ │   │
│  │  │ (.pdf/.md/.docx/.txt)  │ │   │
│  │  │         │              │ │   │
│  │  │         ▼              │ │   │
│  │  │  AI Extraction Engine  │ │   │
│  │  │  (Gemini One-Shot)     │ │   │
│  │  └─────────┬──────────────┘ │   │
│  │            │                 │   │
│  │            ▼                 │   │
│  │  ┌────────────────────────┐ │   │
│  │  │ Preview & Confirm      │ │   │
│  │  │ → Simpan sbg style    │ │   │
│  │  └────────────────────────┘ │   │
│  └─────────────────────────────┘   │
│                                     │
│  session_state["active_style"]      │
│        │                            │
└────────┼────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   PROMPT INJECTION LAYER            │
│                                     │
│  GeminiPromptBuilder.build_*()      │
│       │                             │
│       ├── IF active_style == null:  │
│       │     → Pakai HARDCODED       │
│       │       (format default)      │
│       │                             │
│       └── ELSE:                     │
│             → Inject {FORMAT_SPEC}  │
│               ke dalam prompt       │
│               (replace hardcoded    │
│                structure section)   │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   PERSISTENCE (JSON Lokal)          │
│                                     │
│   data/tor_styles/                  │
│   ├── _default.json    (read-only)  │
│   ├── style_pelatihan.json          │
│   ├── style_pengadaan.json          │
│   └── ...custom styles...          │
│                                     │
│   data/tor_styles/_active.txt       │
│   → berisi ID style yang aktif      │
└─────────────────────────────────────┘
```

### 2.2 Komponen Baru yang Dibangun

| # | Komponen | Lokasi | Deskripsi |
|---|---|---|---|
| 1 | **TOR Style Model** | `app/models/tor_style.py` | Pydantic schema untuk TOR style definition |
| 2 | **Style Manager** | `app/core/style_manager.py` | CRUD + persistence ke JSON files |
| 3 | **Style Extractor** | `app/core/style_extractor.py` | AI-powered extraction dari dokumen referensi |
| 4 | **Prompt Injector** | Modify `gemini_prompt_builder.py` | Dynamic injection format spec ke prompt |
| 5 | **Format Tab UI** | `streamlit_app/components/format_tab.py` | Tab UI baru di Streamlit |
| 6 | **API Endpoints** | `app/api/routes/styles.py` | REST endpoints untuk CRUD styles |

### 2.3 File yang Dimodifikasi (Existing)

| File | Perubahan |
|---|---|
| `app/core/gemini_prompt_builder.py` | Terima `format_spec` parameter, inject ke prompt |
| `app/services/generate_service.py` | Load active style, pass ke prompt builder |
| `app/ai/prompts/generate_tor.py` | Tambah placeholder `{FORMAT_SPEC}` |
| `app/ai/prompts/escalation.py` | Tambah placeholder `{FORMAT_SPEC}` |
| `app/ai/prompts/document_tor.py` | Tambah placeholder `{FORMAT_SPEC}` |
| `streamlit_app/app.py` | Tambah tab "Format TOR" |
| `streamlit_app/config.py` | Tambah path constants |
| `streamlit_app/state.py` | Tambah `active_style_id` ke defaults |
| `streamlit_app/api/client.py` | Tambah API calls untuk styles |

---

## 3. Data Model — TOR Style Schema

### 3.1 TORStyle (Pydantic)

```python
class TORSection(BaseModel):
    """Satu seksi dalam dokumen TOR."""
    id: str                          # "latar_belakang"
    title: str                       # "Latar Belakang"
    heading_level: int = 2           # ## (H2)
    required: bool = True            # Apakah wajib ada di output
    description: str = ""            # Instruksi untuk AI tentang isi seksi ini
    min_paragraphs: int = 1          # Minimum paragraf
    subsections: list[str] = []      # Sub-heading opsional ["2.1 Tujuan Umum", "2.2 Tujuan Khusus"]
    format_hint: str = ""            # "bullet_points" | "paragraphs" | "table" | "mixed"


class TORStyleConfig(BaseModel):
    """Konfigurasi gaya penulisan TOR."""
    language: str = "id"                    # "id" | "en"
    formality: str = "formal"               # "formal" | "semi_formal" | "informal"
    voice: str = "active"                   # "active" | "passive"
    perspective: str = "third_person"       # "first_person" | "third_person"
    min_word_count: int = 500
    max_word_count: int = 3000
    numbering_style: str = "numeric"        # "numeric" (1. 2. 3.) | "roman" (I. II. III.) | "none"
    custom_instructions: str = ""           # Free-form instruksi tambahan dari user


class TORStyle(BaseModel):
    """Definisi lengkap satu TOR style."""
    id: str                                 # UUID atau slug
    name: str                               # "Template Pelatihan Resmi"
    description: str = ""                   # "Format untuk TOR kegiatan pelatihan pemerintah"
    is_default: bool = False                # True hanya untuk _default (read-only)
    is_active: bool = False                 # True = sedang digunakan
    created_at: str                         # ISO datetime
    updated_at: str                         # ISO datetime
    source: str = "manual"                  # "manual" | "extracted" | "default"
    source_filename: str | None = None      # Nama file referensi (jika source=extracted)

    sections: list[TORSection]              # Daftar seksi berurutan
    config: TORStyleConfig                  # Konfigurasi gaya penulisan

    def to_prompt_spec(self) -> str:
        """Serialize menjadi string instruksi siap inject ke prompt."""
        ...
```

### 3.2 Default Style Definition

Berikut mapping **exact** dari hardcoded prompt saat ini ke dalam TORStyle schema:

```json
{
    "id": "_default",
    "name": "Format TOR Standar Pemerintah",
    "description": "Format default bawaan sistem. Mengikuti standar TOR instansi pemerintah Indonesia.",
    "is_default": true,
    "is_active": true,
    "source": "default",

    "sections": [
        {
            "id": "latar_belakang",
            "title": "Latar Belakang",
            "heading_level": 2,
            "required": true,
            "description": "Konteks, alasan kegiatan, dasar hukum jika ada. Min 2 paragraf, kontekstual.",
            "min_paragraphs": 2,
            "format_hint": "paragraphs"
        },
        {
            "id": "tujuan",
            "title": "Tujuan",
            "heading_level": 2,
            "required": true,
            "description": "Tujuan kegiatan. Gunakan kata kerja aktif: Meningkatkan, Membekali, dll.",
            "min_paragraphs": 1,
            "subsections": ["Tujuan Umum", "Tujuan Khusus"],
            "format_hint": "mixed"
        },
        {
            "id": "ruang_lingkup",
            "title": "Ruang Lingkup",
            "heading_level": 2,
            "required": true,
            "description": "Batasan dan cakupan pekerjaan. Meliputi peserta, lokasi, durasi, metode.",
            "min_paragraphs": 1,
            "format_hint": "bullet_points"
        },
        {
            "id": "output",
            "title": "Output / Keluaran",
            "heading_level": 2,
            "required": true,
            "description": "Deliverable yang diharapkan. 3-5 poin konkret.",
            "min_paragraphs": 1,
            "format_hint": "bullet_points"
        },
        {
            "id": "timeline",
            "title": "Timeline / Jadwal Pelaksanaan",
            "heading_level": 2,
            "required": true,
            "description": "Jadwal pelaksanaan. Bisa berupa tabel markdown atau fase dengan durasi.",
            "min_paragraphs": 1,
            "format_hint": "table"
        },
        {
            "id": "estimasi_biaya",
            "title": "Estimasi Biaya",
            "heading_level": 2,
            "required": false,
            "description": "Perkiraan anggaran. Breakdown detail jika data tersedia: No | Komponen | Volume | Satuan | Total.",
            "min_paragraphs": 1,
            "format_hint": "table"
        },
        {
            "id": "penutup",
            "title": "Penutup",
            "heading_level": 2,
            "required": true,
            "description": "Paragraf penutup formal. 1 paragraf.",
            "min_paragraphs": 1,
            "format_hint": "paragraphs"
        }
    ],

    "config": {
        "language": "id",
        "formality": "formal",
        "voice": "active",
        "perspective": "third_person",
        "min_word_count": 500,
        "max_word_count": 3000,
        "numbering_style": "numeric",
        "custom_instructions": "Gunakan Bahasa Indonesia baku sesuai EYD/KBBI. Jangan gunakan placeholder [isi di sini]. Jika data kurang, gunakan asumsi masuk akal dan tandai [ASUMSI]."
    }
}
```

---

## 4. AI Extraction Engine

### 4.1 Tujuan

Ketika user mengupload dokumen TOR referensi (PDF/DOCX/MD/TXT), sistem harus **otomatis memahami** format dan style dokumen tersebut, lalu mengkonversinya menjadi `TORStyle` object.

### 4.2 Extraction Pipeline

```
Upload dokumen referensi
        │
        ▼
┌──────────────────────┐
│ DocumentParser       │
│ (sudah ada di core/) │
│ - PDF → text         │
│ - DOCX → text        │
│ - MD/TXT → text      │
└──────────┬───────────┘
           │ plain text
           ▼
┌──────────────────────┐
│ Gemini One-Shot Call │
│                      │
│ Input:               │
│ - Dokumen text       │
│ - Extraction prompt  │
│                      │
│ Output:              │
│ - JSON TORStyle      │
│   (sections, config) │
└──────────┬───────────┘
           │ parsed JSON
           ▼
┌──────────────────────┐
│ Validator            │
│ - Pydantic parse     │
│ - Fallback defaults  │
│ - Sanitize           │
└──────────┬───────────┘
           │ TORStyle
           ▼
┌──────────────────────┐
│ Preview di UI        │
│ → User edit jika     │
│   perlu              │
│ → User confirm &     │
│   simpan             │
└──────────────────────┘
```

### 4.3 Extraction Prompt (Gemini)

```python
STYLE_EXTRACTION_PROMPT = """Kamu adalah AI yang ahli menganalisis STRUKTUR dan GAYA PENULISAN dokumen formal.

## TUGAS
Analisis dokumen TOR (Term of Reference) berikut dan ekstrak SELURUH informasi tentang FORMAT dan GAYA PENULISAN yang digunakan.

## DOKUMEN SUMBER
---
{DOCUMENT_TEXT}
---

## INSTRUKSI ANALISIS

Identifikasi dengan sangat teliti:

### 1. STRUKTUR SEKSI
- Apa saja nama bab/seksi yang digunakan?
- Bagaimana urutannya?
- Apakah ada subseksi? Jika ya, berapa level?
- Heading level masing-masing (H1/H2/H3)?
- Apakah ada seksi opsional vs wajib?

### 2. GAYA BAHASA
- Formal, semi-formal, atau informal?
- Menggunakan kalimat aktif atau pasif?
- Sudut pandang: orang pertama ("kami"), orang ketiga ("instansi"), atau impersonal?
- Apakah menggunakan jargon spesifik domain tertentu?

### 3. FORMAT KONTEN PER SEKSI
- Apakah isinya berupa paragraf naratif, bullet points, tabel, atau campuran?
- Perkiraan panjang konten per seksi (minimal berapa paragraf)?
- Apakah ada pola numbering tertentu (1.1, 1.2 vs A, B, C vs I, II, III)?

### 4. ELEMEN KHUSUS
- Apakah ada header/footer khusus?
- Apakah ada kop surat atau informasi instansi?
- Apakah ada format penomoran dokumen?
- Instruksi implisit lainnya (misal: selalu mulai dengan dasar hukum)

## FORMAT OUTPUT

Jawab HANYA dalam format JSON valid berikut (tanpa markdown code block):

{
    "extracted_name": "string — nama style yang sesuai dengan dokumen ini",
    "extracted_description": "string — deskripsi singkat tentang format ini",

    "sections": [
        {
            "id": "string — slug unik (snake_case)",
            "title": "string — judul seksi persis seperti dalam dokumen",
            "heading_level": 2,
            "required": true,
            "description": "string — deskripsi apa yang harus diisi di seksi ini (instruksi untuk AI)",
            "min_paragraphs": 1,
            "subsections": ["string — subseksi jika ada"],
            "format_hint": "paragraphs | bullet_points | table | mixed"
        }
    ],

    "config": {
        "language": "id | en",
        "formality": "formal | semi_formal | informal",
        "voice": "active | passive",
        "perspective": "first_person | third_person",
        "min_word_count": 500,
        "max_word_count": 3000,
        "numbering_style": "numeric | roman | none",
        "custom_instructions": "string — instruksi penulisan khusus yang tersirat dari dokumen"
    },

    "analysis_notes": "string — catatan analisis tentang pola unik yang ditemukan"
}
"""
```

### 4.4 Fallback & Error Handling

| Skenario | Penanganan |
|---|---|
| Gemini gagal return JSON valid | Retry 1x dengan prompt repair: "Output kamu bukan JSON valid. Coba lagi." |
| Dokumen bukan TOR (misalnya novel) | Tampilkan warning, tetap coba extract |
| Dokumen terlalu pendek (< 100 kata) | Tolak: "Dokumen terlalu pendek untuk dianalisis." |
| Gemini API offline | Tampilkan error, suruh user isi manual |
| Sections kosong setelah extraction | Fallback ke default sections |

---

## 5. Format Spec → Prompt Injection

### 5.1 Bagaimana TORStyle Menjadi Bagian dari Prompt

Method `TORStyle.to_prompt_spec()` menghasilkan blok teks instruksi yang langsung di-inject ke prompt Gemini.

**Contoh output dari `to_prompt_spec()`:**

```
## FORMAT DOKUMEN TOR (WAJIB DIIKUTI)

Gunakan TEPAT struktur berikut dalam urutan ini:

### Seksi 1: Latar Belakang (heading: ## 1. Latar Belakang)
- WAJIB ada
- Minimal 2 paragraf
- Format: naratif paragraf
- Instruksi: Konteks, alasan kegiatan, dasar hukum jika ada. Min 2 paragraf, kontekstual.

### Seksi 2: Tujuan (heading: ## 2. Tujuan)
- WAJIB ada
- Minimal 1 paragraf
- Sub-heading: Tujuan Umum, Tujuan Khusus
- Format: campuran (paragraf + bullet points)
- Instruksi: Tujuan kegiatan. Gunakan kata kerja aktif.

### Seksi 3: Ruang Lingkup (heading: ## 3. Ruang Lingkup)
- WAJIB ada
- Minimal 1 paragraf
- Format: bullet points
- Instruksi: Batasan dan cakupan pekerjaan.

[...dst untuk setiap seksi...]

## GAYA PENULISAN (WAJIB DIIKUTI)
- Bahasa: Indonesia
- Formalitas: Formal
- Kalimat: Aktif
- Sudut pandang: Orang ketiga
- Penomoran: Numerik (1. 2. 3.)
- Minimal 500 kata, maksimal 3000 kata
- Instruksi tambahan: Gunakan Bahasa Indonesia baku sesuai EYD/KBBI...
```

### 5.2 Injection Point di Prompt

**Sebelum (hardcoded):**
```python
# generate_tor.py
GEMINI_STANDARD_PROMPT = """...
## INSTRUKSI FORMAT
1. Tulis dalam Bahasa Indonesia formal...
2. Gunakan heading markdown: ...
3. Struktur wajib:
   - ## 1. Latar Belakang (min 2 paragraf)
   - ## 2. Tujuan...
   ...
"""
```

**Sesudah (dynamic):**
```python
# generate_tor.py
GEMINI_STANDARD_PROMPT = """Kamu adalah penulis dokumen TOR...

## TUGAS
Buatkan dokumen TOR yang lengkap berdasarkan data berikut:

## DATA INPUT
{DATA_JSON}

## REFERENSI STYLE (dari RAG, jika ada)
{RAG_EXAMPLES}

{FORMAT_SPEC}

## OUTPUT
Tulis langsung dokumen TOR. Jangan tambahkan penjelasan di luar dokumen.
"""
```

`{FORMAT_SPEC}` akan diisi oleh `TORStyle.to_prompt_spec()` saat runtime.

### 5.3 Backward Compatibility

Jika tidak ada style aktif (misalnya `_active.txt` tidak ada atau kosong), sistem **otomatis** menggunakan `_default.json`. Behaviour ini identik dengan kode saat ini — zero breaking change.

---

## 6. Style Manager — CRUD & Persistence

### 6.1 Storage Layout

```
data/
└── tor_styles/
    ├── _default.json          # Bawaan sistem, TIDAK BISA dihapus/diedit
    ├── _active.txt            # Berisi ID style yang aktif (1 line)
    ├── pelatihan_resmi.json   # Custom style 1
    ├── pengadaan_barang.json  # Custom style 2
    └── ...
```

### 6.2 StyleManager API (Python)

```python
class StyleManager:
    """CRUD operations untuk TOR styles."""

    def __init__(self, styles_dir: Path):
        self.dir = styles_dir
        self._ensure_default()

    # --- READ ---
    def list_styles(self) -> list[TORStyle]:
        """Return semua styles, sorted: default pertama, lalu alphabetical."""

    def get_style(self, style_id: str) -> TORStyle:
        """Get satu style by ID."""

    def get_active_style(self) -> TORStyle:
        """Get style yang sedang aktif. Fallback ke default."""

    # --- WRITE ---
    def create_style(self, style: TORStyle) -> TORStyle:
        """Simpan style baru ke JSON file."""

    def update_style(self, style_id: str, updates: dict) -> TORStyle:
        """Update style yang ada. Raise error jika _default."""

    def delete_style(self, style_id: str) -> bool:
        """Hapus style. Raise error jika _default atau sedang aktif."""

    def set_active(self, style_id: str) -> None:
        """Set style sebagai aktif. Simpan ke _active.txt."""

    def duplicate_style(self, style_id: str, new_name: str) -> TORStyle:
        """Duplikasi style (termasuk default) sebagai basis editing."""

    # --- INTERNAL ---
    def _ensure_default(self) -> None:
        """Buat _default.json jika belum ada."""

    def _load(self, style_id: str) -> TORStyle:
        """Load dari JSON file."""

    def _save(self, style: TORStyle) -> None:
        """Save ke JSON file."""
```

### 6.3 Aturan Proteksi Default

| Operasi | Default Style | Custom Style |
|---|---|---|
| View | ✅ | ✅ |
| Edit | ❌ Locked | ✅ |
| Delete | ❌ Locked | ✅ (kecuali sedang aktif) |
| Duplicate | ✅ (jadi custom baru) | ✅ |
| Set Active | ✅ | ✅ |

---

## 7. API Endpoints (Backend)

### 7.1 Routes Baru: `app/api/routes/styles.py`

| Method | Path | Deskripsi |
|---|---|---|
| `GET` | `/api/v1/styles` | List semua styles |
| `GET` | `/api/v1/styles/active` | Get style yang aktif |
| `GET` | `/api/v1/styles/{id}` | Get satu style by ID |
| `POST` | `/api/v1/styles` | Create style baru |
| `PUT` | `/api/v1/styles/{id}` | Update style |
| `DELETE` | `/api/v1/styles/{id}` | Delete style |
| `POST` | `/api/v1/styles/{id}/activate` | Set sebagai aktif |
| `POST` | `/api/v1/styles/{id}/duplicate` | Duplikasi |
| `POST` | `/api/v1/styles/extract` | Upload dokumen → extract style via AI |

### 7.2 Extract Endpoint Detail

```
POST /api/v1/styles/extract
Content-Type: multipart/form-data

Body:
- file: File (PDF/DOCX/MD/TXT) — dokumen TOR referensi
- name: string (opsional) — nama style yang diinginkan

Response (200):
{
    "style": { ...TORStyle object... },
    "analysis_notes": "AI menemukan pola X, Y, Z...",
    "confidence": 0.85
}
```

---

## 8. UI Design — Tab Format TOR

### 8.1 Layout Tab

```
┌─────────────────────────────────────────────────────┐
│  Tab: Format TOR                                     │
│                                                      │
│  ┌─── Style Selector ─────────────────────────────┐ │
│  │ 🎨 Format Aktif: [Format TOR Standar ▾]        │ │
│  │                                                 │ │
│  │ [+ Buat Style Baru]  [📄 Extract dari Dokumen] │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─── Style Detail ───────────────────────────────┐ │
│  │ 📋 Format TOR Standar Pemerintah                │ │
│  │ Default · Tidak bisa diedit                     │ │
│  │                                                 │ │
│  │ ┌── Sections (7) ──────────────────────────┐   │ │
│  │ │                                           │   │ │
│  │ │  1. □ Latar Belakang [wajib]              │   │ │
│  │ │     ↳ paragraf · min 2 paragraf           │   │ │
│  │ │                                           │   │ │
│  │ │  2. □ Tujuan [wajib]                      │   │ │
│  │ │     ↳ campuran · sub: Umum, Khusus        │   │ │
│  │ │                                           │   │ │
│  │ │  3. □ Ruang Lingkup [wajib]               │   │ │
│  │ │     ↳ bullet points                       │   │ │
│  │ │                                           │   │ │
│  │ │  4. □ Output / Keluaran [wajib]           │   │ │
│  │ │     ↳ bullet points                       │   │ │
│  │ │                                           │   │ │
│  │ │  5. □ Timeline [wajib]                    │   │ │
│  │ │     ↳ tabel                               │   │ │
│  │ │                                           │   │ │
│  │ │  6. □ Estimasi Biaya [opsional]            │   │ │
│  │ │     ↳ tabel                               │   │ │
│  │ │                                           │   │ │
│  │ │  7. □ Penutup [wajib]                     │   │ │
│  │ │     ↳ paragraf                            │   │ │
│  │ │                                           │   │ │
│  │ └───────────────────────────────────────────┘   │ │
│  │                                                 │ │
│  │ ┌── Gaya Penulisan ────────────────────────┐   │ │
│  │ │ Bahasa: Indonesia                         │   │ │
│  │ │ Formalitas: Formal                        │   │ │
│  │ │ Suara: Aktif                              │   │ │
│  │ │ Perspektif: Orang ketiga                  │   │ │
│  │ │ Numbering: Numerik (1. 2. 3.)             │   │ │
│  │ │ Kata: 500 — 3000                          │   │ │
│  │ │ Instruksi: "Gunakan Bahasa Indonesia..."  │   │ │
│  │ └──────────────────────────────────────────┘   │ │
│  │                                                 │ │
│  │ [📋 Duplikasi Sebagai Baru]                     │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 8.2 Mode Editor (untuk Custom Style)

Ketika user memilih/membuat custom style, section detail berubah menjadi mode **editable**:

- **Nama & Deskripsi**: Text input
- **Seksi**: Bisa ditambah, dihapus, diurutkan ulang (drag/sort via index)
- **Per seksi**:
  - Judul: text input
  - Wajib/Opsional: toggle
  - Format hint: selectbox (paragraphs/bullet_points/table/mixed)
  - Min paragraf: number input
  - Subsections: text input (comma separated)
  - Instruksi AI: text area
- **Gaya Penulisan**: Semua field editable via selectbox/slider
- **Custom Instructions**: Large text area
- **Tombol**: [💾 Simpan] [🗑️ Hapus Style] [Set Aktif]

### 8.3 Mode Extract (Upload TOR Referensi)

1. User klik "📄 Extract dari Dokumen"
2. File uploader muncul (accept: .pdf, .md, .txt, .docx)
3. User upload → spinner "AI sedang menganalisis format dokumen..."
4. Hasil extraction ditampilkan dalam **mode preview** (read-only)
5. User bisa:
   - **Konfirmasi & Simpan** → style disimpan
   - **Edit dulu** → pindah ke mode editor dengan data pre-filled
   - **Batal** → kembali ke daftar style

---

## 9. PostProcessor Update

### 9.1 Dynamic Section Validation

Saat ini `PostProcessor.EXPECTED_SECTIONS` di-hardcode:

```python
EXPECTED_SECTIONS = [
    "Latar Belakang",
    "Tujuan",
    "Ruang Lingkup",
    "Output",
    "Timeline",
]
```

Setelah perubahan, validation harus **dinamis berdasarkan active style**:

```python
class PostProcessor:
    @staticmethod
    def process(raw_tor: str, style: TORStyle | None = None) -> ProcessedTOR:
        """Validate berdasarkan style sections."""
        content = PostProcessor._clean_formatting(raw_tor)
        word_count = len(content.split())
        has_assumptions = "[ASUMSI]" in content

        # Dynamic section check
        if style:
            expected = [s.title for s in style.sections if s.required]
            min_words = style.config.min_word_count
        else:
            expected = PostProcessor.EXPECTED_SECTIONS
            min_words = PostProcessor.MIN_WORD_COUNT

        missing_sections = PostProcessor._check_structure(content, expected)
        ...
```

---

## 10. Integration Points

### 10.1 GenerateService Flow (Updated)

```python
# SEBELUM
prompt = self.prompt_builder.build_standard(data, rag_examples)

# SESUDAH
active_style = self.style_manager.get_active_style()
format_spec = active_style.to_prompt_spec()
prompt = self.prompt_builder.build_standard(data, rag_examples, format_spec)
```

### 10.2 GeminiPromptBuilder (Updated)

```python
class GeminiPromptBuilder:

    @staticmethod
    def build_standard(
        data: TORData,
        rag_examples: str | None = None,
        format_spec: str | None = None,      # BARU
    ) -> str:
        data_json = data.model_dump_json(indent=2, exclude_none=True)
        prompt = GEMINI_STANDARD_PROMPT.replace("{DATA_JSON}", data_json)

        # Format injection
        if format_spec:
            prompt = prompt.replace("{FORMAT_SPEC}", format_spec)
        else:
            prompt = prompt.replace("{FORMAT_SPEC}", DEFAULT_FORMAT_INSTRUCTIONS)

        # RAG injection (sama seperti sebelumnya)
        ...
        return prompt
```

### 10.3 UI → Backend Flow

```
User pilih style di Tab Format TOR
        │
        ├── POST /api/v1/styles/{id}/activate
        │
        ▼
User trigger generate TOR (via Chat/Direct/Dokumen)
        │
        ├── POST /api/v1/hybrid (atau /generate)
        │
        ▼
GenerateService.generate_tor()
        │
        ├── StyleManager.get_active_style()    ← BARU
        ├── style.to_prompt_spec()              ← BARU
        ├── GeminiPromptBuilder.build_*(data, rag, format_spec)
        ├── Gemini API call
        ├── PostProcessor.process(raw, style)   ← UPDATED
        │
        ▼
TOR dihasilkan sesuai format yang dipilih user
```

---

## 11. Dependency Graph & Task Sequence

```
                    ┌─────────────┐
                    │   Task 01   │
                    │ Data Model  │
                    │ TORStyle    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌───────────┐ ┌───────────┐ ┌───────────┐
        │  Task 02  │ │  Task 03  │ │  Task 04  │
        │  Default  │ │  Style    │ │  Extract  │
        │  Style    │ │  Manager  │ │  Prompt   │
        │  JSON     │ │  CRUD     │ │  (Gemini) │
        └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
              │              │              │
              ▼              ▼              │
        ┌───────────┐ ┌───────────┐        │
        │  Task 05  │ │  Task 06  │        │
        │  Prompt   │ │  API      │        │
        │  Injector │ │  Endpoints│        │
        └─────┬─────┘ └─────┬─────┘        │
              │              │              │
              ▼              ▼              ▼
        ┌─────────────────────────────────────┐
        │           Task 07                    │
        │   Style Extractor Service            │
        │   (Gemini + DocumentParser)          │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 08                    │
        │   PostProcessor Update               │
        │   (Dynamic section validation)       │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 09                    │
        │   GenerateService Integration        │
        │   (Wire everything together)         │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 10                    │
        │   UI: Tab Format TOR                 │
        │   (Style selector, viewer, editor)   │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 11                    │
        │   UI: Extract Flow                   │
        │   (Upload → preview → confirm)       │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 12                    │
        │   Frontend API Client Update         │
        │   (Style endpoints di client.py)     │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 13                    │
        │   E2E Testing & QA                   │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │           Task 14 [BUGFIX]           │
        │   Edit Mode Custom Style             │
        │   + Ikon Material Design             │
        └─────────────────────────────────────┘
```

---

## 12. Task Breakdown Summary

| # | Task | Scope | Estimasi |
|---|---|---|---|
| 01 | Data Model `TORStyle` | `app/models/tor_style.py` | Low |
| 02 | Default Style JSON | `data/tor_styles/_default.json` | Low |
| 03 | Style Manager CRUD | `app/core/style_manager.py` | Medium |
| 04 | Extraction Prompt | `app/ai/prompts/extract_style.py` | Low |
| 05 | Prompt Injector — Dynamic Format | Modify `gemini_prompt_builder.py` + prompts | Medium |
| 06 | API Endpoints | `app/api/routes/styles.py` | Medium |
| 07 | Style Extractor Service | `app/core/style_extractor.py` | Medium |
| 08 | PostProcessor Update | Modify `post_processor.py` | Low |
| 09 | GenerateService Integration | Modify `generate_service.py` | Medium |
| 10 | UI: Tab Format TOR (Viewer + Editor) | `streamlit_app/components/format_tab.py` | High |
| 11 | UI: Extract Flow | Extend format_tab + API integration | Medium |
| 12 | Frontend API Client Update | Modify `streamlit_app/api/client.py` | Low |
| 13 | E2E Testing & QA | Full integration test | Medium |
| 14 | **[BUGFIX]** Edit Mode Custom Style + Ikon Material Design | Modify `streamlit_app/components/format_tab.py` | Medium |

---

## 13. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Gemini extraction menghasilkan JSON invalid | Style tidak tersimpan | Retry 1x + fallback ke manual editor |
| Dokumen referensi bukan TOR | Extract acak | Tampilkan warning + biarkan user edit |
| Format spec terlalu panjang → token overflow | Gemini gagal | Batasi custom_instructions max 500 char, total sections max 15 |
| Style JSON corrupt | App crash | Validasi Pydantic + fallback ke default |
| User hapus style yang sedang aktif | Tidak ada active style | Auto-fallback ke `_default` |

---

## 14. Verification Plan

### 14.1 Unit Tests

- `test_tor_style.py`: Model validation, `to_prompt_spec()` output
- `test_style_manager.py`: CRUD operations, default protection, active switching
- `test_style_extractor.py`: Mock Gemini response → parse → validate

### 14.2 Integration Tests

- Generate TOR dengan default style → output sama seperti sebelum beta 0.1.9
- Generate TOR dengan custom style → output mengikuti custom structure
- Upload dokumen → extract → simpan → generate → verify format match

### 14.3 Manual Verification

- UI visual check: tab baru muncul dan fungsional
- Coba extract dari real TOR PDF → review accuracy
- Switch styles → generate beberapa TOR → bandingkan output

---

## 15. Batasan Scope Beta 0.1.9

| Termasuk | Tidak Termasuk |
|---|---|
| ✅ CRUD styles lokal (JSON) | ❌ Sync styles ke cloud/API |
| ✅ Extract format dari dokumen | ❌ Extract konten (data TOR) dari dokumen |
| ✅ Dynamic prompt injection | ❌ Per-field custom prompt |
| ✅ Global active style | ❌ Per-tab/per-session style |
| ✅ Drag-sort sections (via index) | ❌ Real drag-n-drop (Streamlit limitation) |
| ✅ File-based persistence | ❌ Database persistence |
