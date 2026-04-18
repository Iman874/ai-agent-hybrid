# Task 05 — Gemini Prompt Templates (Standard & Escalation)

## 1. Judul Task

Buat prompt template untuk Gemini: `GEMINI_STANDARD_PROMPT` (generate dari data lengkap) dan `GEMINI_ESCALATION_PROMPT` (generate dari chat history + data parsial).

## 2. Deskripsi

Prompt adalah faktor paling kritikal kualitas output TOR. Task ini membuat dua constant string template yang akan di-inject data JSON (standard) atau chat history (escalation) sebelum dikirim ke Gemini.

## 3. Tujuan Teknis

- `GEMINI_STANDARD_PROMPT` — template untuk generate TOR dari data TORData lengkap
- `GEMINI_ESCALATION_PROMPT` — template untuk generate TOR dari chat history + data parsial
- Placeholder: `{DATA_JSON}`, `{RAG_EXAMPLES}`, `{FULL_CHAT_HISTORY}`
- Instruksi output: Bahasa Indonesia formal, min 500 kata, format heading ##, tag [ASUMSI]

## 4. Scope

### Yang dikerjakan
- `app/ai/prompts/generate_tor.py` — `GEMINI_STANDARD_PROMPT`
- `app/ai/prompts/escalation.py` — `GEMINI_ESCALATION_PROMPT`
- `app/ai/prompts/__init__.py`

### Yang tidak dikerjakan
- PromptBuilder logic (itu task 06)
- Calling Gemini API

## 5. Langkah Implementasi

### Step 1: Buat `app/ai/prompts/__init__.py`

```python
"""Prompt templates untuk Gemini Generator."""
```

### Step 2: Buat `app/ai/prompts/generate_tor.py`

```python
GEMINI_STANDARD_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference / Kerangka Acuan Kerja) profesional untuk instansi pemerintah Indonesia.

## TUGAS
Buatkan dokumen TOR yang lengkap, profesional, dan siap digunakan berdasarkan data berikut:

## DATA INPUT
{DATA_JSON}

## REFERENSI STYLE (dari RAG, jika ada)
{RAG_EXAMPLES}

## INSTRUKSI FORMAT
1. Tulis dalam Bahasa Indonesia formal dan baku (sesuai EYD/KBBI)
2. Gunakan heading markdown: `# TERM OF REFERENCE (TOR)`, `## 1. Latar Belakang`, dst.
3. Struktur wajib:
   - ## 1. Latar Belakang (min 2 paragraf, kontekstual)
   - ## 2. Tujuan (3-5 poin, kata kerja aktif: Meningkatkan, Membekali, dll)
   - ## 3. Ruang Lingkup (peserta, lokasi, durasi, metode)
   - ## 4. Output / Keluaran (3-5 poin konkret)
   - ## 5. Timeline / Jadwal Pelaksanaan (tabel markdown)
   - ## 6. Estimasi Biaya (jika ada data, breakdown detail)
   - ## 7. Penutup (1 paragraf formal)
4. Minimal 500 kata
5. Jangan gunakan placeholder seperti [isi di sini] — isi dengan data yang ada
6. Jika ada data yang kurang, gunakan asumsi masuk akal dan tandai dengan [ASUMSI]

## OUTPUT
Tulis langsung dokumen TOR-nya dalam format markdown. Jangan tambahkan penjelasan di luar dokumen.
"""
```

### Step 3: Buat `app/ai/prompts/escalation.py`

```python
GEMINI_ESCALATION_PROMPT = """Kamu adalah penulis dokumen TOR (Term of Reference) profesional.

## SITUASI
User telah berdiskusi tentang pembuatan TOR tapi percakapan tidak menghasilkan data lengkap. Kamu harus membuat TOR terbaik berdasarkan informasi yang tersedia.

## PERCAKAPAN
{FULL_CHAT_HISTORY}

## INSTRUKSI
1. Analisis percakapan di atas untuk mengekstrak semua informasi yang bisa dijadikan data TOR
2. Untuk informasi yang TIDAK tersedia dalam percakapan, buat asumsi yang masuk akal dan tandai dengan tag [ASUMSI]
3. Tulis dalam Bahasa Indonesia formal dan baku
4. Gunakan heading markdown dengan struktur:
   - # TERM OF REFERENCE (TOR)
   - ## 1. Latar Belakang
   - ## 2. Tujuan
   - ## 3. Ruang Lingkup
   - ## 4. Output / Keluaran
   - ## 5. Timeline / Jadwal Pelaksanaan
   - ## 6. Estimasi Biaya
   - ## 7. Penutup
5. Minimal 400 kata
6. Di akhir dokumen, tambahkan catatan: "Bagian yang ditandai [ASUMSI] dapat disesuaikan sesuai kebutuhan."

## OUTPUT
Tulis langsung dokumen TOR-nya dalam format markdown.
"""
```

### Step 4: Verifikasi

```python
from app.ai.prompts.generate_tor import GEMINI_STANDARD_PROMPT
from app.ai.prompts.escalation import GEMINI_ESCALATION_PROMPT

assert "{DATA_JSON}" in GEMINI_STANDARD_PROMPT
assert "{RAG_EXAMPLES}" in GEMINI_STANDARD_PROMPT
assert "{FULL_CHAT_HISTORY}" in GEMINI_ESCALATION_PROMPT
assert "[ASUMSI]" in GEMINI_ESCALATION_PROMPT
assert "markdown" in GEMINI_STANDARD_PROMPT.lower()

print("ALL PROMPT TEMPLATE TESTS PASSED")
```

## 6. Output yang Diharapkan

Dua file prompt template yang siap di-inject oleh GeminiPromptBuilder.

## 7. Dependencies

- Tidak ada (constant string murni)

## 8. Acceptance Criteria

- [ ] `GEMINI_STANDARD_PROMPT` memiliki placeholder `{DATA_JSON}` dan `{RAG_EXAMPLES}`
- [ ] `GEMINI_ESCALATION_PROMPT` memiliki placeholder `{FULL_CHAT_HISTORY}`
- [ ] Kedua prompt menginstruksikan Bahasa Indonesia formal
- [ ] Kedua prompt menginstruksikan struktur heading ## 1 s/d ## 7
- [ ] Escalation prompt menginstruksikan penggunaan tag `[ASUMSI]`
- [ ] Standard prompt menginstruksikan minimal 500 kata
- [ ] `app/ai/prompts/__init__.py` ada

## 9. Estimasi

**Low** — ~45 menit
