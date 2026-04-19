"""Prompt templat untuk ekstraksi format dokumen TOR menjadi TORStyle JSON."""

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
- Heading level masing-masing (contoh 2 untuk H2, 3 untuk H3)?
- Apakah ada seksi opsional vs wajib?

### 2. GAYA BAHASA
- Formal, semi formal, atau informal?
- Menggunakan kalimat aktif atau pasif?
- Sudut pandang: orang pertama ("kami"), orang ketiga ("instansi"), atau impersonal?
- Apakah menggunakan jargon spesifik domain tertentu?

### 3. FORMAT KONTEN PER SEKSI
- Apakah isinya berupa paragraf naratif, bullet points, tabel, atau campuran?
- Perkiraan panjang konten per seksi (minimal berapa paragraf)?
- Apakah ada pola numbering tertentu (1.1, 1.2 vs A, B, C vs I, II, III)?

### 4. ELEMEN KHUSUS
- Instruksi implisit lainnya (misal: selalu mulai dengan dasar hukum, singkatan perlu dijelaskan)

## FORMAT OUTPUT

Jawab HANYA dalam format JSON valid berikut (TANPA markdown code block awalan ```json):

{
    "extracted_name": "string — nama style yang sesuai dengan dokumen ini, tanpa extension",
    "extracted_description": "string — deskripsi singkat tentang format ini",

    "sections": [
        {
            "id": "string — slug unik lowercase snake_case (cth: latar_belakang)",
            "title": "string — judul seksi persis seperti dalam dokumen",
            "heading_level": 2,
            "required": true,
            "description": "string — deskripsi apa yang wajib diisi di seksi ini (sebagai instruksi prompt untuk AI)",
            "min_paragraphs": 1,
            "subsections": ["string — subseksi jika ada, jika tidak kosongkan list"],
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
        "custom_instructions": "string — instruksi penulisan khusus yang tersirat dari dokumen. Kosongkan jika tidak ada."
    },

    "analysis_notes": "string — catatan analisis proses singkat tentang pola gaya khusus dokumen"
}
"""
